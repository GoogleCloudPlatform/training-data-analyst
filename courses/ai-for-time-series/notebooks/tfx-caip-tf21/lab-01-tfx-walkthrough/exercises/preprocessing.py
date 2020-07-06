# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Covertype preprocessing.
This file defines a template for TFX Transform component.
"""

import tensorflow as tf
import tensorflow_transform as tft

import features

def _fill_in_missing(x):
  """Replace missing values in a SparseTensor.
  Fills in missing values of `x` with '' or 0, and converts to a dense tensor.
  Args:
    x: A `SparseTensor` of rank 2.  Its dense shape should have size at most 1
      in the second dimension.
  Returns:
    A rank 1 tensor where missing values of `x` have been filled in.
  """
  default_value = '' if x.dtype == tf.string else 0
  return tf.squeeze(
      tf.sparse.to_dense(
          tf.SparseTensor(x.indices, x.values, [x.dense_shape[0], 1]),
          default_value),
      axis=1)

def preprocessing_fn(inputs):
  """Preprocesses input columns into transformed columns.
  Preprocesses Covertype Dataset features using Tensorflow Transform library.
  Args:
    inputs(dict): A `dict` of `string` to `Tensor` or `SparseTensor`, where key is a
      Features key in Example proto, value is a Tensor containing the Feature
      proto's value.

  Returns:
    outputs(dict): A `dict` of `string` to `Tensor` or `SparseTensor`, where key is a new set
    of Feature keys, and values are possibly transformed `Tensor` or
    `SparseTensor`.    
    
  """

  outputs = {}

  # Scale numerical features
  for key in features.NUMERIC_FEATURE_KEYS:
    # TODO: your code here to scale numeric features with z-score with Tensorflow Transform.        
    outputs[features.transformed_name(key)] = 

  # Generate vocabularies and maps categorical features
  for key in features.CATEGORICAL_FEATURE_KEYS:
    # TODO: your code here to integerize categorical features and generate vocabulary file with Tensorflow Transform.
    outputs[features.transformed_name(key)] =

  # Convert Cover_Type to dense tensor
  outputs[features.transformed_name(features.LABEL_KEY)] = _fill_in_missing(
      inputs[features.LABEL_KEY])

  return outputs

