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
from tensorflow.contrib.learn.python.learn.utils import (
    saved_model_export_utils, input_fn_utils)


tf.logging.set_verbosity(tf.logging.INFO)

CSV_COLUMNS = ['pickuplon','pickuplat','dropofflon','dropofflat','passengers', 'fare_amount']

LABEL_COLUMN = 'fare_amount'

DEFAULTS = [[-74.0], [40.0], [-74.0], [40.7], [1.0], [0.0]]

# These are the raw input columns, and will be provided for prediction also
INPUT_COLUMNS = [
    # sparse_column_with_keys

    # sparse_column_with_hash_bucket

    # real_valued_column
    layers.real_valued_column('pickuplon'),
    layers.real_valued_column('pickuplat'),
    layers.real_valued_column('dropofflat'),
    layers.real_valued_column('dropofflon'),
    layers.real_valued_column('passengers'),
]

def build_estimator(model_dir, embedding_size, hidden_units):
  """
     Build an estimator starting from INPUT COLUMNS.
     These include feature transformations and synthetic features.
     The model is a wide-and-deep model.
  """

  # input columns
  (plon, plat, dlon, dlat, pcount) = INPUT_COLUMNS 

  # Sparse base columns.

  # reusable transformations

  # Wide columns and deep columns.
  wide_columns = [
      # feature crosses

      # sparse columns with keys

      # anything with a linear relationship
      pcount 
  ]

  deep_columns = [
      # embedding_column

      # real_valued_column
      plat, plon, dlat, dlon
  ]

  return tf.contrib.learn.DNNLinearCombinedRegressor(
      model_dir=model_dir,
      linear_feature_columns=wide_columns,
      dnn_feature_columns=deep_columns,
      dnn_hidden_units=hidden_units or [128, 32, 4])


serving_input_fn = input_fn_utils.build_parsing_serving_input_fn(
    layers.create_feature_spec_for_parsing(INPUT_COLUMNS)
)


def generate_input_fn(filename, num_epochs=None, batch_size=512):
  def _input_fn():
    # could be a path to one file or a file pattern.
    # input_file_names = tf.train.match_filenames_once(filename)
    input_file_names = [filename]  # FIXME

    filename_queue = tf.train.string_input_producer(
        input_file_names, num_epochs=num_epochs, shuffle=True)
    reader = tf.TextLineReader()
    _, value = reader.read_up_to(filename_queue, num_records=batch_size)

    value_column = tf.expand_dims(value, -1)

    columns = tf.decode_csv(value_column, record_defaults=DEFAULTS)

    features = dict(zip(CSV_COLUMNS, columns))

    label = features.pop(LABEL_COLUMN)

    return features, label

  return _input_fn

