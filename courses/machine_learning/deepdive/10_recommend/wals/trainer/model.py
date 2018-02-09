#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import shutil
import numpy as np
import tensorflow as tf
from tensorflow.contrib.factorization import WALSMatrixFactorization

tf.logging.set_verbosity(tf.logging.INFO)

CSV_COLUMNS = 'userId,itemId,rating'.split(',')
DEFAULTS = [[0L], [0L], [0.0]]

import tensorflow as tf
from tensorflow.contrib.factorization import WALSMatrixFactorization
CSV_COLUMNS = 'userId,itemId,rating'.split(',')
DEFAULTS = [[0L], [0L], [0.0]]

def create_features(users, items, ratings, n_users, n_items):
  input_rows = tf.stack( [users, items], axis=1 )
  input_cols = tf.stack( [items, users], axis=1 )
  features = {
    WALSMatrixFactorization.INPUT_ROWS: tf.SparseTensor(input_rows, ratings, (n_users, n_items)),
    WALSMatrixFactorization.INPUT_COLS: tf.SparseTensor(input_cols, ratings, (n_items, n_users)),
    WALSMatrixFactorization.PROJECT_ROW: tf.constant(True)
  }
  return features

def read_dataset(filename, mode, args):
    if mode == tf.estimator.ModeKeys.TRAIN:
        num_epochs = None # indefinitely
    else:
        num_epochs = 1 # end-of-input after this

    # the actual input function passed to TensorFlow
    def _input_fn():
        # could be a path to one file or a file pattern.
        input_file_names = tf.train.match_filenames_once(filename)
        filename_queue = tf.train.string_input_producer(
            input_file_names, shuffle=True, num_epochs=num_epochs)

        # read CSV
        reader = tf.TextLineReader()
        _, value = reader.read_up_to(filename_queue, num_records=args['batch_size'])
        #value_column = tf.expand_dims(value, -1)
        columns = tf.decode_csv(value, record_defaults=DEFAULTS)
        columns = dict(zip(CSV_COLUMNS, columns))

        # WALS needs int64
        users = tf.cast(columns['userId'], dtype=tf.int64)
        items = tf.cast(columns['itemId'], dtype=tf.int64)
        features = create_features(users, items, columns['rating'], args['n_users'], args['n_items'])
        return features, None

    return _input_fn

def create_serving_input_fn(args):
  def serving_input_fn():
    feature_ph = {
        'userId': tf.placeholder(tf.int64, 1)
    }
    # we will have to project all items for this user and initial rating doesn't matter
    items = tf.range(args['n_items'], dtype=tf.int64)
    users = feature_ph['userId'] * tf.ones([args['n_items']], dtype=tf.int64)
    ratings = 0.1 * tf.ones_like(users, dtype=tf.float32)
    features = create_features(users, items, ratings, 1, args['n_items'])
    return tf.contrib.learn.InputFnOps(features, None, feature_ph)
  return serving_input_fn


def train_and_evaluate(args):
    train_steps = int(0.5 + (1.0 * args['num_epochs'] * args['n_interactions']) / args['batch_size'])
    steps_in_epoch = int(0.5 + (1.0 * args['n_interactions']) / args['batch_size'])
    print('Will train for {} steps, evaluating once every {} steps'.format(train_steps, steps_in_epoch))
    def experiment_fn(output_dir):
        return tf.contrib.learn.Experiment(
            tf.contrib.factorization.WALSMatrixFactorization(
                         num_rows=args['n_users'], num_cols=args['n_items'],
                         embedding_dimension=args['n_embeds'],
                         model_dir=args['output_dir']),
            train_input_fn=read_dataset(args['train_path'], tf.estimator.ModeKeys.TRAIN, args),
            eval_input_fn=read_dataset(args['train_path'], tf.estimator.ModeKeys.EVAL, args),
            train_steps=train_steps,
            eval_steps=1,
            min_eval_frequency=steps_in_epoch,
            export_strategies=tf.contrib.learn.utils.saved_model_export_utils.make_export_strategy(serving_input_fn=create_serving_input_fn(args))
    )

    from tensorflow.contrib.learn.python.learn import learn_runner
    learn_runner.run(experiment_fn, args['output_dir'])

