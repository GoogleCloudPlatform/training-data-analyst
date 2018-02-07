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

        # in the format required by WALS
        columns['userId'] = tf.cast(columns['userId'], dtype=tf.int64)
        columns['itemId'] = tf.cast(columns['itemId'], dtype=tf.int64)
        input_rows = tf.stack( [columns['userId'], columns['itemId']], axis=1 )
        input_cols = tf.stack( [columns['itemId'], columns['userId']], axis=1 )
        features = {
                     WALSMatrixFactorization.INPUT_ROWS:
                         tf.SparseTensor(input_rows,
                                         columns['rating'],
                                         (args['n_users'], args['n_items'])),
                     WALSMatrixFactorization.INPUT_COLS:
                         tf.SparseTensor(input_cols,
                                         columns['rating'],
                                         (args['n_items'], args['n_users'])),
                     WALSMatrixFactorization.PROJECT_ROW: tf.constant(True)
                   }
        return features, None
  
    return _input_fn

def serving_input_fn():
    feature_ph = {
        'userId': tf.placeholder(tf.int64, [None])
    }
    features = {
        WALSMatrixFactorization.INPUT_ROWS: feature_ph['userId'],
        WALSMatrixFactorization.PROJECT_ROW: tf.constant(True)  # get items for userId
    }
    return tf.estimator.export.ServingInputReceiver(features, feature_ph)

from tensorflow.contrib.learn.python.learn.utils import saved_model_export_utils

# won't work until WALS inherits from tf.estimator and not tf.contrib.learn.Estimator ...
def train_and_evaluate_estimator(args):
    train_steps = int(0.5 + (1.0 * args['num_epochs'] * args['n_interactions']) / args['batch_size'])
    print('Will train for {} steps'.format(train_steps))
    estimator = WALSMatrixFactorization(
                         num_rows=args['n_users'], num_cols=args['n_items'],
                         embedding_dimension=args['n_embeds'],
                         model_dir=args['output_dir'])
    train_spec=tf.estimator.TrainSpec(
                         input_fn=read_dataset(args['train_path'], tf.estimator.ModeKeys.TRAIN, args),
                         max_steps=train_steps)
    exporter = tf.estimator.LatestExporter('exporter',serving_input_fn)
    eval_spec=tf.estimator.EvalSpec(
                         input_fn=read_dataset(args['train_path'], tf.estimator.ModeKeys.EVAL, args),
                         steps=None,
                         start_delay_secs=1, # start evaluating after N seconds
                         throttle_secs=10,  # evaluate every N seconds
                         exporters=exporter)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)


# implement train_and_evaluate using Experiment
# needed because WALS is a tf.contrib.learn.Estimator 
def train_and_evaluate(args):
    train_steps = int(0.5 + (1.0 * args['num_epochs'] * args['n_interactions']) / args['batch_size'])
    print('Will train for {} steps'.format(train_steps))
    def experiment_fn(output_dir):
        return tf.contrib.learn.Experiment(
            tf.contrib.factorization.WALSMatrixFactorization(
                         num_rows=args['n_users'], num_cols=args['n_items'],
                         embedding_dimension=args['n_embeds'],
                         model_dir=args['output_dir']),
            train_input_fn=read_dataset(args['train_path'], tf.estimator.ModeKeys.TRAIN, args),
            eval_input_fn=read_dataset(args['train_path'], tf.estimator.ModeKeys.EVAL, args),
            export_strategies=[saved_model_export_utils.make_export_strategy(
               serving_input_fn,
               default_output_alternative_key=None,
               exports_to_keep=1
            )],
            train_steps=train_steps,
            eval_steps=None
    )
   
    from tensorflow.contrib.learn.python.learn import learn_runner
    learn_runner.run(experiment_fn, args['output_dir'])

