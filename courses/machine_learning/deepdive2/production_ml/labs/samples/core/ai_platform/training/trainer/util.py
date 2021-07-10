# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities to download and pre-process the data.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

import pandas as pd
from pandas.compat import StringIO

from sklearn.preprocessing import StandardScaler

import tensorflow as tf
from tensorflow.python.lib.io import file_io


def create_dataset(dataset, window_size = 1):
    data_X, data_y = [], []
    df = pd.DataFrame(dataset)
    columns = [df.shift(i) for i in reversed(range(1, window_size+1))]
    data_X = pd.concat(columns, axis=1).dropna().values
    data_y = df.shift(-window_size).dropna().values
    return data_X, data_y

def load_data(data_file_url, window_size):
    """Loads data into preprocessed (train_X, train_y, eval_X, eval_y) dataframes.

    Returns:
      A tuple (train_X, train_y, eval_X, eval_y), where train_X and eval_X are
      Pandas dataframes with features for training and train_y and eval_y are
      numpy arrays with the corresponding labels.
    """
    # The % of data we should use for training
    TRAINING_SPLIT = 0.8

    # Download CSV and import into Pandas DataFrame
    file_stream = file_io.FileIO(data_file_url, mode='r')
    df = pd.read_csv(StringIO(file_stream.read()))
    df.index = df[df.columns[0]]
    df = df[['count']]

    scaler = StandardScaler()

    # Time series: split latest data into test set
    train = df.values[:int(TRAINING_SPLIT * len(df)), :]
    print(train)
    train = scaler.fit_transform(train)
    test = df.values[int(TRAINING_SPLIT * len(df)):, :]
    test = scaler.transform(test)

    # Create test and training sets
    train_X, train_y = create_dataset(train, window_size)
    test_X, test_y = create_dataset(test, window_size)

    # Reshape input data
    train_X = np.reshape(train_X, (train_X.shape[0], 1, train_X.shape[1]))
    test_X = np.reshape(test_X, (test_X.shape[0], 1, test_X.shape[1]))

    return train_X, train_y, test_X, test_y
