# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Trains a Keras model to predict income bracket from other Census data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os

from . import model
from . import util

import tensorflow as tf


def get_args():
    """Argument parser.

    Returns:
      Dictionary of arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--job-dir',
        type=str,
        required=True,
        help='local or GCS location for writing checkpoints and exporting '
             'models')
    parser.add_argument(
        '--num-epochs',
        type=int,
        default=20,
        help='number of times to go through the data, default=20')
    parser.add_argument(
        '--batch-size',
        default=128,
        type=int,
        help='number of records to read during each training step, default=128')
    parser.add_argument(
        '--learning-rate',
        default=.01,
        type=float,
        help='learning rate for gradient descent, default=.01')
    parser.add_argument(
        '--verbosity',
        choices=['DEBUG', 'ERROR', 'FATAL', 'INFO', 'WARN'],
        default='INFO')
    args, _ = parser.parse_known_args()
    return args


def train_and_evaluate(args):
    """Trains and evaluates the Keras model.

    Uses the Keras model defined in model.py and trains on data loaded and
    preprocessed in util.py. Saves the trained model in TensorFlow SavedModel
    format to the path defined in part by the --job-dir argument.

    Args:
      args: dictionary of arguments - see get_args() for details
    """

    train_x, train_y, eval_x, eval_y = util.load_data()

    # dimensions
    num_train_examples, input_dim = train_x.shape
    num_eval_examples = eval_x.shape[0]

    # Create the Keras Model
    keras_model = model.create_keras_model(
        input_dim=input_dim, learning_rate=args.learning_rate)

    # Pass a numpy array by passing DataFrame.values
    training_dataset = model.input_fn(
        features=train_x.values,
        labels=train_y,
        shuffle=True,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size)

    # Pass a numpy array by passing DataFrame.values
    validation_dataset = model.input_fn(
        features=eval_x.values,
        labels=eval_y,
        shuffle=False,
        num_epochs=args.num_epochs,
        batch_size=num_eval_examples)

    # Setup Learning Rate decay.
    lr_decay_cb = tf.keras.callbacks.LearningRateScheduler(
        lambda epoch: args.learning_rate + 0.02 * (0.5 ** (1 + epoch)),
        verbose=True)

    # Setup TensorBoard callback.
    tensorboard_cb = tf.keras.callbacks.TensorBoard(
        os.path.join(args.job_dir, 'keras_tensorboard'),
        histogram_freq=1)

    # Train model
    keras_model.fit(
        training_dataset,
        steps_per_epoch=int(num_train_examples / args.batch_size),
        epochs=args.num_epochs,
        validation_data=validation_dataset,
        validation_steps=1,
        verbose=1,
        callbacks=[lr_decay_cb, tensorboard_cb])

    export_path = os.path.join(args.job_dir, 'keras_export')
    tf.keras.models.save_model(keras_model, export_path)
    print('Model exported to: {}'.format(export_path))


if __name__ == '__main__':
    strategy = tf.distribute.MirroredStrategy()
    with strategy.scope():
        args = get_args()
        tf.compat.v1.logging.set_verbosity(args.verbosity)
        train_and_evaluate(args)
