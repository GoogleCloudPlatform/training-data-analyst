from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import pandas as pd
import numpy as np
import re

from tensorflow.python.keras.preprocessing import sequence
from tensorflow.python.keras.preprocessing import text
from tensorflow.python.keras import models
from tensorflow.python.keras.layers import Dense
from tensorflow.python.keras.layers import Dropout
from tensorflow.python.keras.layers import Embedding
from tensorflow.python.keras.layers import SeparableConv1D
from tensorflow.python.keras.layers import MaxPooling1D
from tensorflow.python.keras.layers import GlobalAveragePooling1D

from google.cloud import storage

# Limit on the number of features (vocabulary size). We use the top 20K words.
TOP_K = 20000
# Limit on the length of text sequences. Sequences longer than this
# will be truncated. Sequences shorter than this will be padded
MAX_SEQUENCE_LENGTH = 50
# Numpy random number seed
SEED = 123

def download_from_gcs(data_path):
    search = re.search('gs://(.*?)/(.*)',data_path)
    bucket_name = search.group(1)
    blob_name = search.group(2)
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    bucket.blob(blob_name).download_to_filename(blob_name)
    return blob_name #this is the local path the file was downloaded to

def load_hacker_news_data(train_data_path,eval_data_path,num_classes):
    if train_data_path.startswith('gs://'):
        train_data_path = download_from_gcs(train_data_path)    
    if eval_data_path.startswith('gs://'):
        eval_data_path = download_from_gcs(eval_data_path)

    # Parse CSV using pandas
    column_names = ('label', 'text')
    classes = {'github': 0, 'nytimes': 1, 'techcrunch': 2}
    df_train = pd.read_csv(train_data_path, names=column_names, sep='\t')
    df_eval = pd.read_csv(eval_data_path, names=column_names, sep='\t')

    return ((list(df_train['text']), np.array(df_train['label'].map(classes))),
            (list(df_eval['text']), np.array(df_eval['label'].map(classes))))

def input_fn(texts, labels, tokenizer, mode):
    print('input_fn: mode: {}'.format(mode))

    # Vectorize training and validation texts.
    x = tokenizer.texts_to_sequences(texts)


    # Fix sequence length to max value. Sequences shorter than the length are
    # padded in the beginning and sequences longer are truncated
    # at the beginning.
    x = sequence.pad_sequences(x, maxlen=MAX_SEQUENCE_LENGTH)

    #default settings for training
    num_epochs=None
    shuffle=True

    #override if this is eval
    if mode==tf.estimator.ModeKeys.EVAL:
        num_epochs=1
        shuffle=False
    print('input_fn: x_shape: {}'.format(x.shape))
    print('input_fn: y_shape: {}'.format(labels.shape))

    return tf.estimator.inputs.numpy_input_fn(
        x={'embedding_1_input': x}, #feature name must match internal keras input name
        y=labels,
        batch_size=128,
        num_epochs=num_epochs,
        shuffle=shuffle,
        queue_capacity=5000
    )

#build estimator from keras model
def keras_estimator(model_dir,
                    config,
                    learning_rate,
                    num_classes,
                    blocks=2,
                    filters=64,
                    dropout_rate=0.2,
                    embedding_dim=200,
                    kernel_size=3,
                    pool_size=3):

    # Create model instance.
    use_pretrained_embedding = False
    is_embedding_trainable = False
    embedding_matrix = None

    model = models.Sequential()

    # Add embedding layer. If pre-trained embedding is used add weights to the
    # embeddings layer and set trainable to input is_embedding_trainable flag.
    if use_pretrained_embedding:
        model.add(Embedding(input_dim=TOP_K,
                            output_dim=embedding_dim,
                            input_length=MAX_SEQUENCE_LENGTH,
                            weights=[embedding_matrix],
                            trainable=is_embedding_trainable))
    else:
        model.add(Embedding(input_dim=TOP_K,
                            output_dim=embedding_dim,
                            input_length=MAX_SEQUENCE_LENGTH))

    for _ in range(blocks - 1):
        model.add(Dropout(rate=dropout_rate))
        model.add(SeparableConv1D(filters=filters,
                                  kernel_size=kernel_size,
                                  activation='relu',
                                  bias_initializer='random_uniform',
                                  depthwise_initializer='random_uniform',
                                  padding='same'))
        model.add(SeparableConv1D(filters=filters,
                                  kernel_size=kernel_size,
                                  activation='relu',
                                  bias_initializer='random_uniform',
                                  depthwise_initializer='random_uniform',
                                  padding='same'))
        model.add(MaxPooling1D(pool_size=pool_size))

    model.add(SeparableConv1D(filters=filters * 2,
                              kernel_size=kernel_size,
                              activation='relu',
                              bias_initializer='random_uniform',
                              depthwise_initializer='random_uniform',
                              padding='same'))
    model.add(SeparableConv1D(filters=filters * 2,
                              kernel_size=kernel_size,
                              activation='relu',
                              bias_initializer='random_uniform',
                              depthwise_initializer='random_uniform',
                              padding='same'))
    model.add(GlobalAveragePooling1D())
    model.add(Dropout(rate=dropout_rate))
    model.add(Dense(num_classes, activation='softmax'))

    # Compile model with learning parameters.
    optimizer = tf.keras.optimizers.Adam(lr=learning_rate)
    model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['acc'])
    estimator = tf.keras.estimator.model_to_estimator(keras_model=model,model_dir=model_dir,config=config)

    return estimator


"""Can't use keras pre_processing functions here because they don't work on tensors
def serving_input_fn():
    feature_placeholders = {
        'embedding_1_input': tf.placeholder(tf.string, [None])
    }
    vectorized = tokenizer.texts_to_sequences(feature_placeholders['embedding_1_input'])
    vectorized = sequence.pad_sequences(vectorized, maxlen=MAX_SEQUENCE_LENGTH)
    features = {
        'embedding_1_input': vectorized
    }

    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)
"""

def train_and_evaluate(output_dir, hparams):
  NUM_CLASSES = 3

  ####Load Raw Data####
  ((train_texts, train_labels), (test_texts, test_labels)) = load_hacker_news_data(
    hparams['train_data_path'],hparams['eval_data_path'],num_classes=3)

  # Create vocabulary from training corpus.
  tokenizer = text.Tokenizer(num_words=TOP_K)
  tokenizer.fit_on_texts(train_texts)
  
  # Create estimator
  run_config = tf.estimator.RunConfig(save_checkpoints_steps=1000)
  estimator = keras_estimator(
                model_dir=output_dir,
                config=run_config,
                learning_rate=hparams['learning_rate'],
                num_classes = NUM_CLASSES
              )
  train_steps = hparams['num_epochs'] * len(train_texts)/ hparams['batch_size']
  train_spec = tf.estimator.TrainSpec(
                 input_fn = input_fn(
                              train_texts,
                              train_labels,
                              tokenizer,
                              mode=tf.estimator.ModeKeys.TRAIN),
                  max_steps = train_steps
                )
  #exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)
  exporter = None
  eval_spec = tf.estimator.EvalSpec(
                input_fn = input_fn(
                             test_texts, 
                             test_labels, 
                             tokenizer, 
                             mode=tf.estimator.ModeKeys.EVAL),
                 steps = None,
                 exporters = exporter,
                 start_delay_secs=10,
                 throttle_secs=10
               )
  tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)