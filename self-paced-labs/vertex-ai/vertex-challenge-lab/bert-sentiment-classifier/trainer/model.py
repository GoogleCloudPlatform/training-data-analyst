import os
import shutil
import logging

import tensorflow as tf
import tensorflow_text as text
import tensorflow_hub as hub
from official.nlp import optimization  # to create AdamW optimizer

AUTOTUNE = tf.data.AUTOTUNE
SEED = 42


def load_datasets(hparams):
    """Load pre-split tf.datasets.
    Args:
      hparams(dict): A dictionary containing model training arguments.
    Returns:
      raw_train_ds(tf.dataset):
      raw_val_ds(tf.dataset):
      raw_test_ds(tf.dataset):      
    """    

    raw_train_ds = tf.keras.preprocessing.text_dataset_from_directory(
        hparams['data-dir'] + '/train',
        batch_size=hparams['batch-size'],
        validation_split=0.2,
        subset='training',
        seed=seed)    

    raw_val_ds = tf.keras.preprocessing.text_dataset_from_directory(
        hparams['data-dir'] + '/train',
        batch_size=hparams['batch-size'],
        validation_split=0.2,
        subset='validation',
        seed=seed)

    raw_test_ds = tf.keras.preprocessing.text_dataset_from_directory(
        hparams['data-dir'] + '/test',
        batch_size=hparams['batch-size'])
    
    return raw_train_ds, raw_val_ds, test_ds


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
    classifier = tf.keras.layers.Dropout(0.1, name="dropout")(net)
    classifier = tf.keras.layers.Dense(1, activation=None, name='classifier')(net)
    
    model = tf.keras.Model(text_input, net)   
    
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
    train_ds, val_ds, test_ds = load_datasets(hparams)
    
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)     
    
    epochs = hparams['epochs']
    steps_per_epoch = tf.data.experimental.cardinality(train_ds).numpy()
    n_train_steps = steps_per_epoch * epochs
    n_warmup_steps = int(0.1*num_train_steps)    
    
    optimizer = optimization.create_optimizer(init_lr=hparams['initial-learning-rate'],
                                              num_train_steps=n_train_steps,
                                              num_warmup_steps=n_warmup_steps,
                                              optimizer_type='adamw')    
    
    with tf.distribute.MirroredStrategy():
        model = build_model(hparams, optimizer=optimizer)
    
    
    logging.info(model.summary())  
    
    logging.info("Test accuracy: %s", model.evaluate(test_ds))

    # Export Keras model in TensorFlow SavedModel format.
    model.save(hparams['model-dir'])
    
    return history
