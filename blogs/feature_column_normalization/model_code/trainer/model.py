#!/usr/bin/env python

# Copyright 2018 Google Inc. All Rights Reserved.
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

import shutil

import numpy as np
import pandas as pd
import tensorflow as tf

# Read the data.
df = pd.read_csv("https://storage.googleapis.com/ml_universities/california_housing_train.csv", sep=",")
msk = np.random.rand(len(df)) < 0.8
traindf = df[msk]
evaldf = df[~msk]
traindf.head()

def get_normalization_parameters(traindf, features):
  """Get the normalization parameters (E.g., mean, std) for traindf for 
  features. We will use these parameters for training, eval, and serving."""
  
  def _z_score_params(column):
    mean = traindf[column].mean()
    std = traindf[column].std()
    return {'mean': mean, 'std': std}
  
  normalization_parameters = {}
  for column in features:
    normalization_parameters[column] = _z_score_params(column)
  return normalization_parameters

NUMERIC_FEATURES = ['housing_median_age', 'total_rooms', 'total_bedrooms',
                    'population', 'households', 'median_income']
normalization_parameters = get_normalization_parameters(traindf,
                                                        NUMERIC_FEATURES)

def _numeric_column_normalized(column_name, normalizer_fn):
  return tf.feature_column.numeric_column(column_name,
                                          normalizer_fn=normalizer_fn)


# Define your feature columns.
def create_feature_cols(features, use_normalization):
  """Create our feature columns using tf.feature_column. This function will 
  get executed during training, evaluation, and serving."""
  normalized_feature_columns = []
  for column_name in features:
    if use_normalization:
      column_params = normalization_parameters[column_name]
      mean = column_params['mean']
      std = column_params['std']
      def normalize_column(col):  # Use mean, std defined above.
        return (col - mean)/std
      normalizer_fn = normalize_column
    else:
      normalizer_fn = None
    normalized_feature_columns.append(_numeric_column_normalized(column_name,
                                                              normalizer_fn))
  return normalized_feature_columns

def input_fn(df, shuffle=True):
  """For training and evaluation inputs."""
  return tf.estimator.inputs.pandas_input_fn(
    x = df,
    y = df["median_house_value"]/100000,  # Scale target.
    shuffle = shuffle)

def train_and_evaluate(use_normalization, outdir):
  shutil.rmtree(outdir, ignore_errors = True) # start fresh each time
  
  feature_columns = create_feature_cols(NUMERIC_FEATURES, use_normalization)
  
  run_config = tf.estimator.RunConfig(save_summary_steps=10,
                                      model_dir = outdir  # More granular checkpointing for TensorBoard.
                                     )
  model = tf.estimator.LinearRegressor(feature_columns = feature_columns, config=run_config)
  # Training input function.
  train_spec = tf.estimator.TrainSpec(input_fn=input_fn(traindf),
                                      max_steps=1000)

  
  def json_serving_input_fn():
    """Build the serving inputs. For serving real-time predictions
    using ml-engine."""
    inputs = {}
    for feat in feature_columns:
      inputs[feat.name] = tf.placeholder(shape=[None], dtype=feat.dtype)
    return tf.estimator.export.ServingInputReceiver(inputs, inputs)
  
  # Evaluation and serving input function.
  exporter = tf.estimator.FinalExporter('housing', json_serving_input_fn)
  eval_spec = tf.estimator.EvalSpec(input_fn=input_fn(evaldf),
                                    exporters=[exporter],
                                    name='housing-eval')
  # Train and evaluate the model.
  tf.estimator.train_and_evaluate(model, train_spec, eval_spec)
  return model
