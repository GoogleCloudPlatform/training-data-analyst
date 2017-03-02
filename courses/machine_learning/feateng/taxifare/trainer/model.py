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
from tensorflow.contrib import layers
import tensorflow.contrib.learn as tflearn
from tensorflow.contrib import metrics
import numpy as np

tf.logging.set_verbosity(tf.logging.INFO)

CSV_COLUMNS = 'fare_amount,dayofweek,hourofday,pickuplon,pickuplat,dropofflon,dropofflat,passengers,key'.split(',')
SCALE_COLUMNS = ['pickuplon','pickuplat','dropofflon','dropofflat','passengers']
LABEL_COLUMN = 'fare_amount'
KEY_FEATURE_COLUMN = 'key'
DEFAULTS = [[0.0], ['Sun'], [0], [-74.0], [40.0], [-74.0], [40.7], [1.0], ['nokey']]

# These are the raw input columns, and will be provided for prediction also
INPUT_COLUMNS = [
    # define features
    layers.sparse_column_with_keys('dayofweek', keys=['Sun', 'Mon', 'Tues', 'Wed', 'Thu', 'Fri', 'Sat']),
    layers.sparse_column_with_integerized_feature('hourofday', bucket_size=24),

    # engineered features that are created in the input_fn
    layers.real_valued_column('latdiff'),
    layers.real_valued_column('londiff'),
    layers.real_valued_column('euclidean'),

    # real_valued_column
    layers.real_valued_column('pickuplon'),
    layers.real_valued_column('pickuplat'),
    layers.real_valued_column('dropofflat'),
    layers.real_valued_column('dropofflon'),
    layers.real_valued_column('passengers'),
]

def build_estimator(model_dir, nbuckets, hidden_units):
  """
     Build an estimator starting from INPUT COLUMNS.
     These include feature transformations and synthetic features.
     The model is a wide-and-deep model.
  """

  # input columns
  (dayofweek, hourofday, latdiff, londiff, euclidean, plon, plat, dlon, dlat, pcount) = INPUT_COLUMNS 

  # bucketize the lats & lons
  latbuckets = np.linspace(38.0, 42.0, nbuckets).tolist()
  lonbuckets = np.linspace(-76.0, -72.0, nbuckets).tolist()
  b_plat = layers.bucketized_column(plat, latbuckets)
  b_dlat = layers.bucketized_column(dlat, latbuckets)
  b_plon = layers.bucketized_column(plon, lonbuckets)
  b_dlon = layers.bucketized_column(dlon, lonbuckets)

  # feature cross
  ploc = layers.crossed_column([b_plat, b_plon], nbuckets*nbuckets)
  dloc = layers.crossed_column([b_dlat, b_dlon], nbuckets*nbuckets)
  pd_pair = layers.crossed_column([ploc, dloc], nbuckets ** 4 )
  day_hr =  layers.crossed_column([dayofweek, hourofday], 24*7)

  # Wide columns and deep columns.
  wide_columns = [
      # feature crosses
      dloc, ploc, pd_pair,
      day_hr,

      # sparse columns
      dayofweek, hourofday,

      # anything with a linear relationship
      pcount 
  ]

  deep_columns = [
      # embedding_column to "group" together ...
      layers.embedding_column(pd_pair, 10),
      layers.embedding_column(day_hr, 10),

      # real_valued_column
      plat, plon, dlat, dlon,
      latdiff, londiff, euclidean
  ]

  return tf.contrib.learn.DNNLinearCombinedRegressor(
      model_dir=model_dir,
      linear_feature_columns=wide_columns,
      dnn_feature_columns=deep_columns,
      dnn_hidden_units=hidden_units or [128, 32, 4])

def add_engineered(features):
    # this is how you can do feature engineering in TensorFlow
    lat1 = features['pickuplat']
    lat2 = features['dropofflat']
    lon1 = features['pickuplon']
    lon2 = features['dropofflon']
    latdiff = (lat1 - lat2)
    londiff = (lon1 - lon2)
    # set features for distance with sign that indicates direction
    features['latdiff'] = latdiff
    features['londiff'] = londiff
    dist = tf.sqrt(latdiff*latdiff + londiff*londiff)
    features['euclidean'] = dist
    return features   

def serving_input_fn():
    feature_placeholders = {
        # all the real-valued columns
        column.name: tf.placeholder(tf.float32, [None]) for column in INPUT_COLUMNS[2:]
    }
    feature_placeholders['dayofweek'] = tf.placeholder(tf.string, [None])
    feature_placeholders['hourofday'] = tf.placeholder(tf.int32, [None])
  
    features = {
      key: tf.expand_dims(tensor, -1)
      for key, tensor in feature_placeholders.items()
    }
    return tflearn.utils.input_fn_utils.InputFnOps(
      add_engineered(features),
      None,
      feature_placeholders
    )


def generate_csv_input_fn(filename, num_epochs=None, batch_size=512, mode=tf.contrib.learn.ModeKeys.TRAIN):
  def _input_fn():
    # could be a path to one file or a file pattern.
    input_file_names = tf.train.match_filenames_once(filename)
    #input_file_names = [filename]

    filename_queue = tf.train.string_input_producer(
        input_file_names, num_epochs=num_epochs, shuffle=True)
    reader = tf.TextLineReader()
    _, value = reader.read_up_to(filename_queue, num_records=batch_size)

    value_column = tf.expand_dims(value, -1)

    columns = tf.decode_csv(value_column, record_defaults=DEFAULTS)

    features = dict(zip(CSV_COLUMNS, columns))

    label = features.pop(LABEL_COLUMN)

    return add_engineered(features), label

  return _input_fn

def gzip_reader_fn():
  return tf.TFRecordReader(options=tf.python_io.TFRecordOptions(
      compression_type=tf.python_io.TFRecordCompressionType.GZIP))

def generate_tfrecord_input_fn(data_paths, num_epochs=None, batch_size=512, mode=tf.contrib.learn.ModeKeys.TRAIN):
  def get_input_features():
    # Read the tfrecords. Same input schema as in preprocess
    input_schema = {}
    if mode != tf.contrib.learn.ModeKeys.INFER:
      input_schema[LABEL_COLUMN] = tf.FixedLenFeature(shape=[1], dtype=tf.float32, default_value=0.0)
    for name in ['dayofweek', 'key']:
      input_schema[name] = tf.FixedLenFeature(shape=[1], dtype=tf.string, default_value='null')
    for name in ['hourofday']:
      input_schema[name] = tf.FixedLenFeature(shape=[1], dtype=tf.int64, default_value=0)
    for name in SCALE_COLUMNS:
      input_schema[name] = tf.FixedLenFeature(shape=[1], dtype=tf.float32, default_value=0.0)

    # how? 
    keys, features = tf.contrib.learn.io.read_keyed_batch_features(
        data_paths[0] if len(data_paths) == 1 else data_paths,
        batch_size,
        input_schema,
        reader=gzip_reader_fn,
        reader_num_threads=4,
        queue_capacity=batch_size * 2,
        randomize_input=(mode != tf.contrib.learn.ModeKeys.EVAL),
        num_epochs=(1 if mode == tf.contrib.learn.ModeKeys.EVAL else num_epochs))
    target = features.pop(LABEL_COLUMN)
    features[KEY_FEATURE_COLUMN] = keys
    return add_engineered(features), target

  # Return a function to input the features into the model from a data path.
  return get_input_features



def get_eval_metrics():
  return {
     'rmse': tflearn.MetricSpec(metric_fn=metrics.streaming_root_mean_squared_error),
     'training/hptuning/metric': tflearn.MetricSpec(metric_fn=metrics.streaming_root_mean_squared_error),
  }
