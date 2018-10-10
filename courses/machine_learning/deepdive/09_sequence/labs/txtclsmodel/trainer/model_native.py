from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import pandas as pd
import numpy as np
import re
import os

from tensorflow.python.keras.preprocessing import text
from tensorflow.python.keras import models
from tensorflow.python.keras.layers import Dense
from tensorflow.python.keras.layers import Dropout
from tensorflow.python.keras.layers import Embedding
from tensorflow.python.keras.layers import Conv1D
from tensorflow.python.keras.layers import MaxPooling1D
from tensorflow.python.keras.layers import GlobalAveragePooling1D

from google.cloud import storage

tf.logging.set_verbosity(tf.logging.INFO)

CLASSES = {'github': 0, 'nytimes': 1, 'techcrunch': 2}  # label-to-int mapping
TOP_K = 20000  # Limit on the number vocabulary size used for tokenization
MAX_SEQUENCE_LENGTH = 50  # Sentences will be truncated/padded to this length
VOCAB_FILE_PATH = None # where vocabulary is saved, dynamically set in train_and_eval function
PADWORD = 'ZYXW'

"""
Helper function to download data from Google Cloud Storage
  # Arguments:
      source: string, the GCS URL to download from (e.g. 'gs://bucket/file.csv')
      destination: string, the filename to save as on local disk. MUST be filename
      ONLY, doesn't support folders. (e.g. 'file.csv', NOT 'folder/file.csv')
  # Returns: nothing, downloads file to local disk
"""
def download_from_gcs(source, destination):
    search = re.search('gs://(.*?)/(.*)', source)
    bucket_name = search.group(1)
    blob_name = search.group(2)
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    bucket.blob(blob_name).download_to_filename(destination)


"""
Parses raw tsv containing hacker news headlines and returns (sentence, integer label) pairs
  # Arguments:
      train_data_path: string, path to tsv containing training data.
        can be a local path or a GCS url (gs://...)
      eval_data_path: string, path to tsv containing eval data.
        can be a local path or a GCS url (gs://...)
  # Returns:
      ((train_sentences, train_labels), (test_sentences, test_labels)):  sentences
        are lists of strings, labels are numpy integer arrays
"""
def load_hacker_news_data(train_data_path, eval_data_path):
    if train_data_path.startswith('gs://'):
        download_from_gcs(train_data_path, destination='train.csv')
        train_data_path = 'train.csv'
    if eval_data_path.startswith('gs://'):
        download_from_gcs(eval_data_path, destination='eval.csv')
        eval_data_path = 'eval.csv'

    # Parse CSV using pandas
    column_names = ('label', 'text')
    df_train = pd.read_csv(train_data_path, names=column_names, sep='\t')
    df_eval = pd.read_csv(eval_data_path, names=column_names, sep='\t')

    return ((list(df_train['text']), np.array(df_train['label'].map(CLASSES))),
            (list(df_eval['text']), np.array(df_eval['label'].map(CLASSES))))


"""
Create tf.estimator compatible input function
  # Arguments:
      texts: [strings], list of sentences
      labels: numpy int vector, integer labels for sentences
      batch_size: int, number of records to use for each train batch
      mode: tf.estimator.ModeKeys.TRAIN or tf.estimator.ModeKeys.EVAL 
  # Returns:
      tf.data.Dataset, produces feature and label
        tensors one batch at a time
"""
def input_fn(texts, labels, batch_size, mode):
    # Convert texts from python strings to tensors
    x = tf.constant(texts)

    # Map text to sequence of word-integers and pad
    x = vectorize_sentences(x)

    # Create tf.data.Dataset from tensors
    dataset = tf.data.Dataset.from_tensor_slices((x, labels))

    # Pad to constant length
    dataset = dataset.map(pad)

    if mode == tf.estimator.ModeKeys.TRAIN:
        num_epochs = None #loop indefinitley
        dataset = dataset.shuffle(buffer_size=50000) # our input is already shuffled so this is redundant
    else:
        num_epochs = 1

    dataset = dataset.repeat(num_epochs).batch(batch_size)
    return dataset

"""
Given an int tensor, remove 0s then pad to a fixed length representation. 
  #Arguments:
    feature: int tensor 
    label: int. not used in function, just passed through
  #Returns:
    (int tensor, int) tuple.
"""
def pad(feature, label):
    # 1. Remove 0s which represent out of vocabulary words
    nonzero_indices = tf.where(tf.not_equal(feature, tf.zeros_like(feature)))
    without_zeros = tf.gather(feature,nonzero_indices)
    without_zeros = tf.squeeze(without_zeros, axis=1)

    # 2. Prepend 0s till MAX_SEQUENCE_LENGTH
    padded = tf.pad(without_zeros, [[MAX_SEQUENCE_LENGTH, 0]])  # pad out with zeros
    padded = padded[-MAX_SEQUENCE_LENGTH:]  # slice to constant length
    return (padded, label)


"""
Given sentences, return an integer representation
  # Arguments:
      sentences: string tensor of shape (?,), contains sentences to vectorize
  # Returns:
      Integer representation of the sentence. Word-integer mapping is determined
        by VOCAB_FILE_PATH. Words out of vocabulary will map to 0
"""
def vectorize_sentences(sentences):
    # 1. Remove punctuation
    sentences = tf.regex_replace(sentences, '[[:punct:]]', ' ')

    # 2. Split string tensor into component words
    words = tf.string_split(sentences)
    words = tf.sparse_tensor_to_dense(words, default_value=PADWORD)

    # 3. Map each word to respective integer
    table = tf.contrib.lookup.index_table_from_file(
        vocabulary_file=VOCAB_FILE_PATH,
        num_oov_buckets=0,
        vocab_size=None,
        default_value=0,  # for words not in vocabulary (OOV)
        key_column_index=0,
        value_column_index=1,
        delimiter=',')
    numbers = table.lookup(words)

    return numbers


"""
Builds a CNN model using keras and converts to tf.estimator.Estimator
  # Arguments
      model_dir: string, file path where training files will be written
      config: tf.estimator.RunConfig, specifies properties of tf Estimator
      filters: int, output dimension of the layers.
      kernel_size: int, length of the convolution window.
      embedding_dim: int, dimension of the embedding vectors.
      dropout_rate: float, percentage of input to drop at Dropout layers.
      pool_size: int, factor by which to downscale input at MaxPooling layer.
      embedding_path: string , file location of pre-trained embedding (if used)
        defaults to None which will cause the model to train embedding from scratch
      word_index: dictionary, mapping of vocabulary to integers. used only if
        pre-trained embedding is provided

    # Returns
        A tf.estimator.Estimator 
"""
def keras_estimator(model_dir,
                    config,
                    learning_rate,
                    filters=64,
                    dropout_rate=0.2,
                    embedding_dim=200,
                    kernel_size=3,
                    pool_size=3,
                    embedding_path=None,
                    word_index=None):
    # Create model instance.
    model = models.Sequential()
    num_features = min(len(word_index) + 1, TOP_K)

    # Add embedding layer. If pre-trained embedding is used add weights to the
    # embeddings layer and set trainable to input is_embedding_trainable flag.
    if embedding_path != None:
        embedding_matrix = get_embedding_matrix(word_index, embedding_path, embedding_dim)
        is_embedding_trainable = True  # set to False to freeze embedding weights

        model.add(Embedding(input_dim=num_features,
                            output_dim=embedding_dim,
                            input_length=MAX_SEQUENCE_LENGTH,
                            weights=[embedding_matrix],
                            trainable=is_embedding_trainable))
    else:
        model.add(Embedding(input_dim=num_features,
                            output_dim=embedding_dim,
                            input_length=MAX_SEQUENCE_LENGTH))

    model.add(Dropout(rate=dropout_rate))
    model.add(Conv1D(filters=filters,
                              kernel_size=kernel_size,
                              activation='relu',
                              bias_initializer='random_uniform',
                              padding='same'))

    model.add(MaxPooling1D(pool_size=pool_size))
    model.add(Conv1D(filters=filters * 2,
                              kernel_size=kernel_size,
                              activation='relu',
                              bias_initializer='random_uniform',
                              padding='same'))
    model.add(GlobalAveragePooling1D())
    model.add(Dropout(rate=dropout_rate))
    model.add(Dense(len(CLASSES), activation='softmax'))

    # Compile model with learning parameters.
    optimizer = tf.keras.optimizers.Adam(lr=learning_rate)
    model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['acc'])
    estimator = tf.keras.estimator.model_to_estimator(keras_model=model, model_dir=model_dir, config=config)

    return estimator


"""
Defines the features to be passed to the model during inference
  Can pass in string text directly. Tokenization done in serving_input_fn 
  # Arguments: none
  # Returns: tf.estimator.export.ServingInputReceiver
"""
def serving_input_fn():
    feature_placeholder = tf.placeholder(tf.string, [None])
    features = vectorize_sentences(feature_placeholder)
    return tf.estimator.export.TensorServingInputReceiver(features, feature_placeholder)


"""
Takes embedding for generic vocabulary and extracts the embeddings
  matching the current vocabulary
  The pre-trained embedding file is obtained from https://nlp.stanford.edu/projects/glove/
  # Arguments: 
      word_index: dict, {key =word in vocabulary: value= integer mapped to that word}
      embedding_path: string, location of the pre-trained embedding file on disk
      embedding_dim: int, dimension of the embedding space
  # Returns: numpy matrix of shape (vocabulary, embedding_dim) that contains the embedded
      representation of each word in the vocabulary.
"""
def get_embedding_matrix(word_index, embedding_path, embedding_dim):
    # Read the pre-trained embedding file and get word to word vector mappings.
    embedding_matrix_all = {}

    # Download if embedding file is in GCS
    if embedding_path.startswith('gs://'):
        download_from_gcs(embedding_path, destination='embedding.csv')
        embedding_path = 'embedding.csv'

    with open(embedding_path) as f:
        for line in f:  # Every line contains word followed by the vector value
            values = line.split()
            word = values[0]
            coefs = np.asarray(values[1:], dtype='float32')
            embedding_matrix_all[word] = coefs

    # Prepare embedding matrix with just the words in our word_index dictionary
    num_words = min(len(word_index) + 1, TOP_K)
    embedding_matrix = np.zeros((num_words, embedding_dim))

    for word, i in word_index.items():
        if i >= TOP_K:
            continue
        embedding_vector = embedding_matrix_all.get(word)
        if embedding_vector is not None:
            # words not found in embedding index will be all-zeros.
            embedding_matrix[i] = embedding_vector
    return embedding_matrix


"""
Main orchestrator. Responsible for calling all other functions in model.py
  # Arguments: 
      output_dir: string, file path where training files will be written
      hparams: dict, command line parameters passed from task.py
  # Returns: nothing, kicks off training and evaluation
"""
def train_and_evaluate(output_dir, hparams):
    # Load Data
    ((train_texts, train_labels), (test_texts, test_labels)) = load_hacker_news_data(
        hparams['train_data_path'], hparams['eval_data_path'])

    # Create vocabulary from training corpus.
    tokenizer = text.Tokenizer(num_words=TOP_K)
    tokenizer.fit_on_texts(train_texts)

    # Generate vocabulary file from tokenizer object to enable
    # creating a native tensorflow lookup table later (see vectorize_sentences())
    tf.gfile.MkDir(output_dir) # directory must exist before we can use tf.gfile.open
    global VOCAB_FILE_PATH; VOCAB_FILE_PATH = os.path.join(output_dir,'vocab.txt')
    with tf.gfile.Open(VOCAB_FILE_PATH, 'wb') as f:
        f.write("{},0\n".format(PADWORD))  # map padword to 0
        for word, index in tokenizer.word_index.items():
            if index < TOP_K: # only save mappings for TOP_K words
                f.write("{},{}\n".format(word, index))

    # Create estimator
    run_config = tf.estimator.RunConfig(save_checkpoints_steps=500)
    estimator = keras_estimator(
        model_dir=output_dir,
        config=run_config,
        learning_rate=hparams['learning_rate'],
        embedding_path=hparams['embedding_path'],
        word_index=tokenizer.word_index
    )

    # Create TrainSpec
    train_steps = hparams['num_epochs'] * len(train_texts) / hparams['batch_size']
    train_spec = tf.estimator.TrainSpec(
        input_fn=lambda:input_fn(
            train_texts,
            train_labels,
            hparams['batch_size'],
            mode=tf.estimator.ModeKeys.TRAIN),
        max_steps=train_steps
    )

    # Create EvalSpec
    exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)
    eval_spec = tf.estimator.EvalSpec(
        input_fn=lambda:input_fn(
            test_texts,
            test_labels,
            hparams['batch_size'],
            mode=tf.estimator.ModeKeys.EVAL),
        steps=None,
        exporters=exporter,
        start_delay_secs=10,
        throttle_secs=10
    )

    # Start training
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
