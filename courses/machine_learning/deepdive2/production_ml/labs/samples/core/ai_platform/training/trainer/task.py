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
"""Utility functions to parse command-line arguments and train model
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import tensorflow as tf
from tensorflow import keras
from tensorflow.contrib.training.python.training import hparam

from . import model
from . import util


def get_args():
    """Argument parser.

    Returns:
      Dictionary of arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data-file-url',
        type=str,
        default='gs://chicago-crime/reports.csv',
        help='url of data file to download')
    parser.add_argument(
        '--job-dir',
        type=str,
        required=True,
        help='local or GCS location for writing checkpoints and exporting models')
    parser.add_argument(
        '--num-epochs',
        type=int,
        default=250,
        help='number of times to go through the data, default=100')
    parser.add_argument(
        '--batch-size',
        default=128,
        type=int,
        help='number of records to read during each training step, default=128')
    parser.add_argument(
        '--window-size',
        type=int,
        default=14,
        help='number of observations, default=14')
    parser.add_argument(
        '--learning-rate',
        default=.001,
        type=float,
        help='learning rate for gradient descent, default=.001')
    parser.add_argument(
        '--verbosity',
        choices=['DEBUG', 'ERROR', 'FATAL', 'INFO', 'WARN'],
        default='INFO')
    return parser.parse_args()


def train_and_evaluate(hparams):
    """Trains and evaluates the Keras model.

    Uses the Keras model defined in model.py and trains on data loaded and
    preprocessed in util.py. Saves the trained model in TensorFlow SavedModel
    format to the path defined in part by the --job-dir argument.

    Args:
      hparams: dictionary of hyperparameters - see get_args() for details
    """

    train_X, train_y, eval_X, eval_y = util.load_data(hparams.data_file_url, hparams.window_size)

    # Dimensions
    num_train_examples, input_dim, _ = train_X.shape
    num_eval_examples = eval_X.shape[0]

    # Create the Keras Model
    keras_model = model.create_keras_model(
        input_dim=input_dim, learning_rate=hparams.learning_rate, window_size=hparams.window_size)

    # Pass a numpy array by passing DataFrame.values
    training_dataset = model.input_fn(
        features=train_X,
        labels=train_y,
        shuffle=False,
        num_epochs=hparams.num_epochs,
        batch_size=hparams.batch_size)

    # Pass a numpy array by passing DataFrame.values
    validation_dataset = model.input_fn(
        features=eval_X,
        labels=eval_y,
        shuffle=False,
        num_epochs=hparams.num_epochs,
        batch_size=num_eval_examples)

    # Callback to write events for TensorBoard analysis
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=hparams.job_dir, batch_size=hparams.batch_size)

    # Train model
    keras_model.fit(
        training_dataset,
        steps_per_epoch=int(num_train_examples / hparams.batch_size),
        epochs=hparams.num_epochs,
        validation_data=validation_dataset,
        validation_steps=1,
        verbose=1,
        shuffle=False,
        callbacks=[tensorboard_callback]
    )

    export_path = tf.contrib.saved_model.save_keras_model(
        keras_model, hparams.job_dir)
    export_path = export_path.decode('utf-8')
    print('Model exported to: ', export_path)


if __name__ == '__main__':
    args = get_args()
    tf.logging.set_verbosity(args.verbosity)
    hyperparams = hparam.HParams(**args.__dict__)
    train_and_evaluate(hyperparams)
