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
import tensorflow as tf
import tensorflow.contrib.layers as tflayers
from tensorflow.contrib.learn.python.learn import learn_runner
import tensorflow.contrib.metrics as metrics


tf.logging.set_verbosity(tf.logging.INFO)

BUCKET = None  # set from task.py
PATTERN = 'of' # gets all files
TRAIN_STEPS = 10000
CSV_COLUMNS = 'weight_pounds,is_male,mother_age,mother_race,plurality,gestation_weeks,mother_married,cigarette_use,alcohol_use,key'.split(',')
LABEL_COLUMN = 'weight_pounds'
KEY_COLUMN = 'key'
DEFAULTS = [[0.0], ['null'], [0.0], ['null'], [0.0], [0.0], ['null'], ['null'], ['null'], ['nokey']]

def read_dataset(prefix, batch_size=512):
  # use prefix to create filename
  filename = 'gs://{}/babyweight/preproc/{}*{}*'.format(BUCKET, prefix, PATTERN)
  print(filename)
  if prefix == 'train':
    mode = tf.contrib.learn.ModeKeys.TRAIN
  else:
    mode = tf.contrib.learn.ModeKeys.EVAL
    
  # the actual input function passed to TensorFlow
  def _input_fn():
    # could be a path to one file or a file pattern.
    input_file_names = tf.train.match_filenames_once(filename)
    filename_queue = tf.train.string_input_producer(
        input_file_names, shuffle=True)
 
    # read CSV
    reader = tf.TextLineReader()
    _, value = reader.read_up_to(filename_queue, num_records=batch_size)
    value_column = tf.expand_dims(value, -1)
    columns = tf.decode_csv(value_column, record_defaults=DEFAULTS)
    features = dict(zip(CSV_COLUMNS, columns))
    features.pop(KEY_COLUMN)
    label = features.pop(LABEL_COLUMN)
    return features, label
  
  return _input_fn

def get_wide_deep():
  # define column types
  races = ['White', 'Black', 'American Indian', 'Chinese', 
           'Japanese', 'Hawaiian', 'Filipino', 'Unknown',
           'Asian Indian', 'Korean', 'Samaon', 'Vietnamese']
  is_male,mother_age,mother_race,plurality,gestation_weeks,mother_married,cigarette_use,alcohol_use = \
      [ \
          tflayers.sparse_column_with_keys('is_male', keys=['True', 'False']),
          tflayers.real_valued_column('mother_age'),
          tflayers.sparse_column_with_keys('mother_race', keys=races),
          tflayers.real_valued_column('plurality'),
          tflayers.real_valued_column('gestation_weeks'),
          tflayers.sparse_column_with_keys('mother_married', keys=['True', 'False']),
          tflayers.sparse_column_with_keys('cigarette_use', keys=['True', 'False', 'None']),
          tflayers.sparse_column_with_keys('alcohol_use', keys=['True', 'False', 'None'])
      ]

  # which columns are wide (sparse, linear relationship to output) and which are deep (complex relationship to output?)  
  wide = [is_male,
          mother_race,
          plurality,
          mother_married,
          cigarette_use,
          alcohol_use]
  deep = [mother_age,
          gestation_weeks,
          tflayers.embedding_column(mother_race, 3)]
  return wide, deep


def serving_input_fn():
    feature_placeholders = {
      'is_male': tf.placeholder(tf.string, [None]),
      'mother_age': tf.placeholder(tf.float32, [None]),
      'mother_race': tf.placeholder(tf.string, [None]),
      'plurality': tf.placeholder(tf.float32, [None]),
      'gestation_weeks': tf.placeholder(tf.float32, [None]),
      'mother_married': tf.placeholder(tf.string, [None]),
      'cigarette_use': tf.placeholder(tf.string, [None]),
      'alcohol_use': tf.placeholder(tf.string, [None])
    }
    features = {
      key: tf.expand_dims(tensor, -1)
      for key, tensor in feature_placeholders.items()
    }
    return tf.contrib.learn.utils.input_fn_utils.InputFnOps(
      features,
      None,
      feature_placeholders)


from tensorflow.contrib.learn.python.learn.utils import saved_model_export_utils
def experiment_fn(output_dir):
    wide, deep = get_wide_deep()
    return tf.contrib.learn.Experiment(
        tf.contrib.learn.DNNLinearCombinedRegressor(model_dir=output_dir,
                                                    linear_feature_columns=wide,
                                                    dnn_feature_columns=deep,
                                                    dnn_hidden_units=[64, 32]),
        train_input_fn=read_dataset('train'),
        eval_input_fn=read_dataset('eval'),
        eval_metrics={
            'rmse': tf.contrib.learn.MetricSpec(
                metric_fn=metrics.streaming_root_mean_squared_error
            )
        },
        export_strategies=[saved_model_export_utils.make_export_strategy(
            serving_input_fn,
            default_output_alternative_key=None,
            exports_to_keep=1
        )],
        train_steps=TRAIN_STEPS
    )
