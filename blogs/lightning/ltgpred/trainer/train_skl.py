#!/usr/bin/env python
"""Train model to predict lightning using scikit-learn.

Copyright Google Inc.
2018 Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required
by applicable law or agreed to in writing, software distributed under the
License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.
"""
from __future__ import division
from __future__ import print_function
import argparse
import copy
import datetime
import logging
import os
import subprocess
import hypertune
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
import tensorflow as tf
from tensorflow.python.lib.io import file_io


def read_csv_file(filename):
  """reads CSV file into a Pandas dataframe.

  Args:
    filename (str): Name of CSV file, can be gs:// URLs also

  Returns:
    Pandas dataframe
  """
  with file_io.FileIO(filename, 'r') as f:
    logging.info('Reading %s', filename)
    df = pd.read_csv(
        f,
        header=None,
        names=[
            'cx', 'cy', 'lat', 'lon', 'mean_ref_sm', 'max_ref_sm',
            'mean_ref_big', 'max_ref_big', 'ltg_sm', 'ltg_big', 'has_ltg'
        ])
    df['has_ltg'] = df['has_ltg'].astype(float)
    return df


def read_csv_files(filename_pattern):
  """reads CSV files specified by a pattern into a Pandas dataframe.

  Args:
    filename_pattern (str): Wildcard of CSV files, can be gs:// URLs also

  Returns:
    Pandas dataframe
  """
  filenames = tf.gfile.Glob(filename_pattern)
  dataframes = [read_csv_file(filename) for filename in filenames]
  df = pd.concat(dataframes)
  logging.info('Read in %d examples from %d files matching %s', len(df),
               len(filenames), filename_pattern)
  return df


def input_fn(indf):
  df = copy.deepcopy(indf)
  # features, label
  label = df['has_ltg']
  del df['has_ltg']
  features = pd.get_dummies(df)
  return features, label


def train_and_evaluate(params, max_depth=5, n_estimators=100):
  """Main train and evaluate loop.

  Args:
    params (dict): Command-line parameters passed in
    max_depth (int): Maximum depth of a tree in random forest
    n_estimators (int): Number of trees in random forest
  Returns:
    estimator, rmse
  """
  # train
  train_df = read_csv_files(params['train_data'])
  train_x, train_y = input_fn(train_df)
  model = RandomForestClassifier(
      max_depth=max_depth, n_estimators=n_estimators, random_state=0)
  model.fit(train_x, train_y)

  # evaluate
  eval_df = read_csv_files(params['eval_data'])
  eval_x, eval_y = input_fn(eval_df)
  eval_pred = model.predict(eval_x)
  rmserr = np.sqrt(np.mean((eval_pred - eval_y) * (eval_pred - eval_y)))
  logging.info('Eval rmse=%f', rmserr)
  return model, rmserr


def save_model(model_tosave, gcspath, name):  # pylint: disable=unused-argument
  filename = 'model.joblib'
  joblib.dump(model_tosave, filename)
  model_path = os.path.join(
      gcspath,
      datetime.datetime.now().strftime('export_%Y%m%d_%H%M%S'), filename)
  subprocess.check_call(['gsutil', 'cp', filename, model_path])
  return model_path


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Train scikit-learn model for lightning prediction')
  parser.add_argument(
      '--job-dir', required=True, help='output dir. could be local or on GCS')
  parser.add_argument(
      '--train_data',
      required=True,
      help='Pattern for training data files. could be local or on GCS')
  parser.add_argument(
      '--eval_data',
      required=True,
      help='Pattern for evaluation data files. could be local or on GCS')

  logging.basicConfig(level=getattr(logging, 'INFO', None))
  options = parser.parse_args().__dict__

  # train
  estimator, rmse = train_and_evaluate(options)
  loc = save_model(estimator, options['job_dir'], 'lightning_skl')

  # for hyperparameter tuning
  hpt = hypertune.HyperTune()
  hpt.report_hyperparameter_tuning_metric(
      hyperparameter_metric_tag='rmse', metric_value=rmse, global_step=0)
