# Copyright 2020 Google LLC
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
"""Trains a Keras model to predict baby weight."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import datetime
import os

from . import model

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
        '--bucket',
        type=str,
        required=True,
        help='GCS bucket where you stored the training data')
    parser.add_argument(
        '--num-train-examples',
        type=int,
        default=100000,
        help='number of examples to train the model, default=100000')
    parser.add_argument(
        '--num-eval-examples',
        type=int,
        default=10000,
        help='number of examples to evaluate the model, default=10000')
    parser.add_argument(
        '--num-evals',
        type=int,
        default=20,
        help='number of evaluations during the training, default=20')
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
    Uses the Keras model defined in model.py and trains on data
    loaded in model.py. Saves the trained model in TensorFlow
    SavedModel format to the path defined in part by the --job-dir
    argument.
    Args:
      args: dictionary of arguments - see get_args() for details
    """

    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    # Create the Keras Model
    keras_model = model.create_keras_model(learning_rate=args.learning_rate)

    # Create the dataset generator
    training_dataset = model.read_dataset(args.bucket, 'train', '', args.batch_size)
    validation_dataset = model.read_dataset(args.bucket, 'eval', '', args.batch_size,
            eval=True).take(args.num_eval_examples//args.batch_size)

    # Setup TensorBoard callback.
    tensorboard_cb = tf.keras.callbacks.TensorBoard(
        os.path.join(args.job_dir, 'tensorboard', ts),
        histogram_freq=1)

    # Train model
    keras_model.fit(
        training_dataset,
        steps_per_epoch=args.num_train_examples//(args.batch_size*args.num_evals),
        epochs=args.num_evals,
        validation_data=validation_dataset,
        verbose=1,
        callbacks=[tensorboard_cb])

    export_path = os.path.join(args.job_dir, 'export', ts)
    keras_model.save(export_path, save_format="tf")
    print('Model exported to: {}'.format(export_path))


if __name__ == '__main__':
    args = get_args()
    tf.compat.v1.logging.set_verbosity(args.verbosity)
    train_and_evaluate(args)
