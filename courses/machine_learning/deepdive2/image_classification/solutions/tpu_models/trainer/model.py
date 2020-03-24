import os
import shutil

import tensorflow as tf
from tensorflow.keras import callbacks
from tensorflow.keras import layers
from tensorflow.keras import models

import tensorflow_hub as hub

from . import util

NCLASSES = len(util.CLASS_NAMES)
LEARNING_RATE = 0.0001
DROPOUT = .2


def build_model(output_dir, hub_handle):
    """Compiles keras model for image classification."""
    model = models.Sequential([
        hub.KerasLayer(hub_handle, trainable=False),
        layers.Dropout(rate=DROPOUT),
        layers.Dense(
            NCLASSES,
            activation='softmax',
            kernel_regularizer=tf.keras.regularizers.l2(LEARNING_RATE))
    ])
    model.build((None,)+(util.IMG_HEIGHT, util.IMG_WIDTH, util.IMG_CHANNELS))
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy'])
    return model


def train_and_evaluate(
    model, num_epochs, steps_per_epoch, train_data, eval_data, output_dir):
    """Compiles keras model and loads data into it for training."""
    model_callbacks = []
    if output_dir:
        tensorboard_callback = callbacks.TensorBoard(log_dir=output_dir)
        model_callbacks = [tensorboard_callback]

    history = model.fit(
        train_data,
        validation_data=eval_data,
        validation_steps=util.VALIDATION_STEPS,
        epochs=num_epochs,
        steps_per_epoch=steps_per_epoch,
        callbacks=model_callbacks)

    if output_dir:
        export_path = os.path.join(output_dir, 'keras_export')
        model.save(export_path, save_format='tf')

    return history
