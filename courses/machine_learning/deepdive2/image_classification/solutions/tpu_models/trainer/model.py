import os
import shutil

import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.layers import Dense, Dropout
import tensorflow_hub as hub

from . import util

NCLASSES = len(util.CLASS_NAMES)
LEARNING_RATE = 0.0001
DROPOUT = .2


def build_model(output_dir, hub_handle):
    """Compiles keras model for image classification."""
    model = tf.keras.Sequential([
        hub.KerasLayer(hub_handle, trainable=False),
        tf.keras.layers.Dropout(rate=DROPOUT),
        tf.keras.layers.Dense(
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
    callbacks = []
    if output_dir:
        tensorboard_callback = TensorBoard(log_dir=output_dir)
        callbacks = [tensorboard_callback]

    history = model.fit(
        train_data,
        validation_data=eval_data,
        validation_steps=util.VALIDATION_STEPS,
        epochs=num_epochs,
        steps_per_epoch=steps_per_epoch,
        callbacks=callbacks)

    if output_dir:
        export_path = os.path.join(output_dir, 'keras_export')
        model.save(export_path, save_format='tf')

    return history
