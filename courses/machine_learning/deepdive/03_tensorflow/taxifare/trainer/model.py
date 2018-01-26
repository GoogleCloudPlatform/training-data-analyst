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

import tensorflow as tf
import numpy as np
import shutil

tf.logging.set_verbosity(tf.logging.INFO)

CSV_COLUMNS = ['fare_amount', 'pickuplon','pickuplat','dropofflon','dropofflat','passengers', 'key']
LABEL_COLUMN = 'fare_amount'
DEFAULTS = [[0.0], [-74.0], [40.0], [-74.0], [40.7], [1.0], ['nokey']]

def read_dataset(filename, batch_size=512, mode=tf.estimator.ModeKeys.TRAIN):
  def _input_fn():
    if mode == tf.estimator.ModeKeys.TRAIN:
        num_epochs = None # indefinitely
    else:
        num_epochs = 1 # end-of-input after this
        
    input_file_names = tf.train.match_filenames_once(filename)
    filename_queue = tf.train.string_input_producer(
        input_file_names, num_epochs=num_epochs, shuffle=True)
    reader = tf.TextLineReader()
    _, value = reader.read_up_to(filename_queue, num_records=batch_size)
    if mode == tf.estimator.ModeKeys.TRAIN:
          value = tf.train.shuffle_batch([value], batch_size, capacity=10*batch_size, 
                                         min_after_dequeue=batch_size, enqueue_many=True, 
                                         allow_smaller_final_batch=False)
    
    value_column = tf.expand_dims(value, -1)
    columns = tf.decode_csv(value_column, record_defaults=DEFAULTS)
    features = dict(zip(CSV_COLUMNS, columns))
    label = features.pop(LABEL_COLUMN)
    return features, label

  return _input_fn


INPUT_COLUMNS = [
    tf.feature_column.numeric_column('pickuplon'),
    tf.feature_column.numeric_column('pickuplat'),
    tf.feature_column.numeric_column('dropofflat'),
    tf.feature_column.numeric_column('dropofflon'),
    tf.feature_column.numeric_column('passengers'),
]

def add_more_features(feats):
  # nothing to add (yet!)
  return feats

feature_cols = add_more_features(INPUT_COLUMNS)


def serving_input_fn():
    feature_placeholders = {
        column.name: tf.placeholder(tf.float32, [None]) for column in INPUT_COLUMNS
    }
    features = {
      key: tf.expand_dims(tensor, -1)
      for key, tensor in feature_placeholders.items()
    }
    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)


def train_and_evaluate(args):
    estimator = tf.estimator.DNNRegressor(
                         model_dir=args['output_dir'],
                         feature_columns=feature_cols,
                         hidden_units=args['hidden_units'])
    train_spec=tf.estimator.TrainSpec(
                         input_fn=read_dataset(args['train_data_paths'],
                                               batch_size=args['train_batch_size'],
                                               mode=tf.contrib.learn.ModeKeys.TRAIN),
                         max_steps=args['train_steps'])
    exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)
    eval_spec=tf.estimator.EvalSpec(
                         input_fn=read_dataset(args['eval_data_paths'],
                                               batch_size=10000,
                                               mode=tf.contrib.learn.ModeKeys.EVAL),
                         steps=None,
                         start_delay_secs=args['eval_delay_secs'],
                         throttle_secs=args['min_eval_frequency'],
                         exporters=exporter)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

