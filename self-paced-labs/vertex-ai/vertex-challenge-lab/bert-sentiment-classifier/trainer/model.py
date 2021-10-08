import os
import shutil
import logging

import tensorflow as tf
import tensorflow_text as text
import tensorflow_hub as hub
from official.nlp import optimization  # to create AdamW optimizer

DATA_URL = 'https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz'
LOCAL_DATA_DIR = './tmp/data'
AUTOTUNE = tf.data.AUTOTUNE
SEED = 42


def download_data(data_dir):
    """Download dataset."""
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    dataset = tf.keras.utils.get_file(
      fname='aclImdb_v1.tar.gz',
      origin=DATA_URL,
      untar=True,
      cache_dir=data_dir,
      cache_subdir="")
    
    dataset_dir = os.path.join(os.path.dirname(dataset), 'aclImdb')
    
    train_dir = os.path.join(dataset_dir, 'train')
    
    # remove unused folders to make it easier to load the data
    remove_dir = os.path.join(train_dir, 'unsup')
    shutil.rmtree(remove_dir)
    
    return dataset_dir


def load_datasets(dataset_dir, hparams):
    """Load pre-split tf.datasets.
    Args:
      hparams(dict): A dictionary containing model training arguments.
    Returns:
      raw_train_ds(tf.dataset):
      raw_val_ds(tf.dataset):
      raw_test_ds(tf.dataset):      
    """    

    raw_train_ds = tf.keras.preprocessing.text_dataset_from_directory(
        os.path.join(dataset_dir, 'train'),
        batch_size=hparams['batch-size'],
        validation_split=0.2,
        subset='training',
        seed=SEED)    

    raw_val_ds = tf.keras.preprocessing.text_dataset_from_directory(
        os.path.join(dataset_dir, 'train'),
        batch_size=hparams['batch-size'],
        validation_split=0.2,
        subset='validation',
        seed=SEED)

    raw_test_ds = tf.keras.preprocessing.text_dataset_from_directory(
        os.path.join(dataset_dir, 'test'),
        batch_size=hparams['batch-size'])
    
    return raw_train_ds, raw_val_ds, raw_test_ds


def build_text_classifier(hparams, optimizer):
    """Train and evaluate TensorFlow BERT sentiment classifier.
    Args:
      hparams(dict): A dictionary containing model training arguments.
    Returns:
      history(tf.keras.callbacks.History): Keras callback that records training event history.
    """
    text_input = tf.keras.layers.Input(shape=(), dtype=tf.string, name='text')
    preprocessor = hub.KerasLayer(hparams['tf-hub-bert-preprocessor'], name='preprocessing')
    encoder_inputs = preprocessor(text_input)
    encoder = hub.KerasLayer(hparams['tf-hub-bert-encoder'], trainable=True, name='BERT_encoder')
    outputs = encoder(encoder_inputs)
    classifier = outputs["pooled_output"]
    classifier = tf.keras.layers.Dropout(hparams['dropout'], name="dropout")(classifier)
    classifier = tf.keras.layers.Dense(1, activation=None, name='classifier')(classifier)
    
    model = tf.keras.Model(text_input, classifier)   
    
    loss = tf.keras.losses.BinaryCrossentropy(from_logits=True)
    metrics = tf.metrics.BinaryAccuracy()    
    
    model.compile(optimizer=optimizer,
                  loss=loss,
                  metrics=metrics)    
    
    return model


def train_evaluate(hparams):
    """Train and evaluate TensorFlow BERT sentiment classifier.
    Args:
      hparams(dict): A dictionary containing model training arguments.
    Returns:
      history(tf.keras.callbacks.History): Keras callback that records training event history.
    """
    dataset_dir = download_data(LOCAL_DATA_DIR)
    train_ds, val_ds, test_ds = load_datasets(dataset_dir, hparams)
    
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)     
    
    epochs = hparams['epochs']
    steps_per_epoch = tf.data.experimental.cardinality(train_ds).numpy()
    n_train_steps = steps_per_epoch * epochs
    n_warmup_steps = int(0.1 * n_train_steps)    
    
    optimizer = optimization.create_optimizer(init_lr=hparams['initial-learning-rate'],
                                              num_train_steps=n_train_steps,
                                              num_warmup_steps=n_warmup_steps,
                                              optimizer_type='adamw')    
    
    mirrored_strategy = tf.distribute.MirroredStrategy()
    with mirrored_strategy.scope():
        model = build_text_classifier(hparams=hparams, optimizer=optimizer)
        logging.info(model.summary())
        
    history = model.fit(x=train_ds,
                        validation_data=val_ds,
                        epochs=epochs)  
    
    logging.info("Test accuracy: %s", model.evaluate(test_ds))

    # Export Keras model in TensorFlow SavedModel format.
    model.save(hparams['model-dir'])
    
    return history
