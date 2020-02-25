# Copyright 2017 Google Inc. All Rights Reserved.
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

"""WALS model core functions."""

import math

import numpy as np
import tensorflow as tf
from tensorflow.contrib.factorization.python.ops import factorization_ops


def get_rmse(output_row, output_col, actual):
  """Compute rmse between predicted and actual ratings.

  Args:
    output_row: evaluated numpy array of row_factor
    output_col: evaluated numpy array of col_factor
    actual: coo_matrix of actual (test) values

  Returns:
    rmse
  """
  mse = 0
  for i in xrange(actual.data.shape[0]):
    row_pred = output_row[actual.row[i]]
    col_pred = output_col[actual.col[i]]
    err = actual.data[i] - np.dot(row_pred, col_pred)
    mse += err * err
  mse /= actual.data.shape[0]
  rmse = math.sqrt(mse)
  return rmse


def simple_train(model, input_tensor, num_iterations):
  """Helper function to train model on input for num_iterations.

  Args:
    model:            WALSModel instance
    input_tensor:     SparseTensor for input ratings matrix
    num_iterations:   number of row/column updates to run

  Returns:
    tensorflow session, for evaluating results
  """
  sess = tf.Session(graph=input_tensor.graph)

  with input_tensor.graph.as_default():
    row_update_op = model.update_row_factors(sp_input=input_tensor)[1]
    col_update_op = model.update_col_factors(sp_input=input_tensor)[1]

    sess.run(model.initialize_op)
    sess.run(model.worker_init)
    for _ in xrange(num_iterations):
      sess.run(model.row_update_prep_gramian_op)
      sess.run(model.initialize_row_update_op)
      sess.run(row_update_op)
      sess.run(model.col_update_prep_gramian_op)
      sess.run(model.initialize_col_update_op)
      sess.run(col_update_op)

  return sess

LOG_RATINGS = 0
LINEAR_RATINGS = 1
LINEAR_OBS_W = 100.0


def make_wts(data, wt_type, obs_wt, feature_wt_exp, axis):
  """Generate observed item weights.

  Args:
    data:             coo_matrix of ratings data
    wt_type:          weight type, LOG_RATINGS or LINEAR_RATINGS
    obs_wt:           linear weight factor
    feature_wt_exp:   logarithmic weight factor
    axis:             axis to make weights for, 1=rows/users, 0=cols/items

  Returns:
    vector of weights for cols (items) or rows (users)
  """
  # recipricol of sum of number of items across rows (if axis is 0)
  frac = np.array(1.0/(data > 0.0).sum(axis))

  # filter any invalid entries
  frac[np.ma.masked_invalid(frac).mask] = 0.0

  # normalize weights according to assumed distribution of ratings
  if wt_type == LOG_RATINGS:
    wts = np.array(np.power(frac, feature_wt_exp)).flatten()
  else:
    wts = np.array(obs_wt * frac).flatten()

  # check again for any numerically unstable entries
  assert np.isfinite(wts).sum() == wts.shape[0]
  return wts


def wals_model(data, dim, reg, unobs, weights=False,
               wt_type=LINEAR_RATINGS, feature_wt_exp=None,
               obs_wt=LINEAR_OBS_W):
  """Create the WALSModel and input, row and col factor tensors.

  Args:
    data:           scipy coo_matrix of item ratings
    dim:            number of latent factors
    reg:            regularization constant
    unobs:          unobserved item weight
    weights:        True: set obs weights, False: obs weights = unobs weights
    wt_type:        feature weight type: linear (0) or log (1)
    feature_wt_exp: feature weight exponent constant
    obs_wt:         feature weight linear factor constant

  Returns:
    input_tensor:   tensor holding the input ratings matrix
    row_factor:     tensor for row_factor
    col_factor:     tensor for col_factor
    model:          WALSModel instance
  """
  row_wts = None
  col_wts = None

  num_rows = data.shape[0]
  num_cols = data.shape[1]

  if weights:
    assert feature_wt_exp is not None
    row_wts = np.ones(num_rows)
    col_wts = make_wts(data, wt_type, obs_wt, feature_wt_exp, 0)

  row_factor = None
  col_factor = None

  with tf.Graph().as_default():

    input_tensor = tf.SparseTensor(indices=zip(data.row, data.col),
                                   values=(data.data).astype(np.float32),
                                   dense_shape=data.shape)

    model = factorization_ops.WALSModel(num_rows, num_cols, dim,
                                        unobserved_weight=unobs,
                                        regularization=reg,
                                        row_weights=row_wts,
                                        col_weights=col_wts)

    # retrieve the row and column factors
    row_factor = model.row_factors[0]
    col_factor = model.col_factors[0]

  return input_tensor, row_factor, col_factor, model
