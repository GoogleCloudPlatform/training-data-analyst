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

import tensorflow as tf
import numpy as np
import shutil

tf.logging.set_verbosity(tf.logging.INFO)

# List the CSV columns
CSV_COLUMNS = ['fare_amount', 'pickuplon','pickuplat','dropofflon','dropofflat','passengers', 'key']

#Choose which column is your label
LABEL_COLUMN = 'fare_amount'

# Set the default values for each CSV column in case there is a missing value
DEFAULTS = [[0.0], [-74.0], [40.0], [-74.0], [40.7], [1.0], ['nokey']]

# Create an input function that stores your data into a dataset
def read_dataset(filename, mode, batch_size = 512):
    def _input_fn():
        def decode_csv(value_column):
            columns = tf.decode_csv(value_column, record_defaults = DEFAULTS)
            features = dict(list(zip(CSV_COLUMNS, columns)))
            label = features.pop(LABEL_COLUMN)
            return features, label
    
        # Create list of files that match pattern
        file_list = tf.gfile.Glob(filename)

        # Create dataset from file list
        dataset = tf.data.TextLineDataset(file_list).map(decode_csv)
        
        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None # indefinitely
            dataset = dataset.shuffle(buffer_size = 10 * batch_size)
        else:
            num_epochs = 1 # end-of-input after this

        dataset = dataset.repeat(num_epochs).batch(batch_size)
        return dataset.make_one_shot_iterator().get_next()
    return _input_fn

# Define your feature columns
INPUT_COLUMNS = [
    tf.feature_column.numeric_column('pickuplon'),
    tf.feature_column.numeric_column('pickuplat'),
    tf.feature_column.numeric_column('dropofflat'),
    tf.feature_column.numeric_column('dropofflon'),
    tf.feature_column.numeric_column('passengers'),
]

# Create a function that will augment your feature set
def add_more_features(feats):
    # Nothing to add (yet!)
    return feats

feature_cols = add_more_features(INPUT_COLUMNS)

# Create your serving input function so that your trained model will be able to serve predictions
def serving_input_fn():
    feature_placeholders = {
        column.name: tf.placeholder(tf.float32, [None]) for column in INPUT_COLUMNS
    }
    features = feature_placeholders
    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)

# Create an estimator that we are going to train and evaluate
def train_and_evaluate(args):
    estimator = tf.estimator.DNNRegressor(
        model_dir = args['output_dir'],
        feature_columns = feature_cols,
        hidden_units = args['hidden_units'])
    train_spec = tf.estimator.TrainSpec(
        input_fn = read_dataset(args['train_data_paths'],
                                batch_size = args['train_batch_size'],
                                mode = tf.estimator.ModeKeys.TRAIN),
        max_steps = args['train_steps'])
    exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)
    eval_spec = tf.estimator.EvalSpec(
        input_fn = read_dataset(args['eval_data_paths'],
                                batch_size = 10000,
                                mode = tf.estimator.ModeKeys.EVAL),
        steps = None,
        start_delay_secs = args['eval_delay_secs'],
        throttle_secs = args['min_eval_frequency'],
        exporters = exporter)
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
