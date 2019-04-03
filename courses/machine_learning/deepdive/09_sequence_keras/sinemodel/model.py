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

tf.logging.set_verbosity(tf.logging.INFO)

TIMESERIES_COL = "height"
N_OUTPUTS = 1  # in each sequence, 1-49 are features, and 50 is label
SEQ_LEN = None
DEFAULTS = None
N_INPUTS = None


def init(hparams):
    global SEQ_LEN, DEFAULTS, N_INPUTS
    SEQ_LEN = hparams["sequence_length"]
    DEFAULTS = [[0.0] for x in range(0, SEQ_LEN)]
    N_INPUTS = SEQ_LEN - N_OUTPUTS


def linear_model(hparams):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_shape = [N_INPUTS], name = TIMESERIES_COL))
    model.add(tf.keras.layers.Dense(units = 1, activation = None))
    return model

              
def dnn_model(hparams):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_shape = [N_INPUTS], name = TIMESERIES_COL))
    model.add(tf.keras.layers.Dense(units = 30, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 10, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 1, activation = None))
    return model

              
def cnn_model(hparams):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_shape = [N_INPUTS], name = TIMESERIES_COL))
    model.add(tf.keras.layers.Reshape(target_shape = [N_INPUTS, 1]))
    model.add(tf.keras.layers.Conv1D(filters = N_INPUTS // 2, kernel_size = 3, padding = "same", activation = tf.nn.relu))
    model.add(tf.keras.layers.MaxPooling1D(pool_size = 2, strides = 2))
    model.add(tf.keras.layers.Conv1D(filters = N_INPUTS // 2, kernel_size = 3, padding = "same", activation = tf.nn.relu))
    model.add(tf.keras.layers.MaxPooling1D(pool_size = 2, strides = 2))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(units = 3, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 1, activation = None))
    return model
              

def rnn_model(hparams):
    CELL_SIZE = N_INPUTS // 3  # size of the internal state in each of the cells

    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_shape = [N_INPUTS], name = TIMESERIES_COL))
    model.add(tf.keras.layers.Reshape(target_shape = [N_INPUTS, 1]))
    model.add(tf.keras.layers.LSTM(units = CELL_SIZE))
    model.add(tf.keras.layers.Dense(units = N_INPUTS // 2, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 1, activation = None))
    return model


# 2-layer RNN
def rnn2_model(hparams):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.InputLayer(input_shape = [N_INPUTS], name = TIMESERIES_COL))
    model.add(tf.keras.layers.Reshape(target_shape = [N_INPUTS, 1]))
    model.add(tf.keras.layers.LSTM(units = N_INPUTS * 2, return_sequences = True))
    model.add(tf.keras.layers.LSTM(units = N_INPUTS // 2))
    model.add(tf.keras.layers.Dense(units = (N_INPUTS // 2) // 2, activation = tf.nn.relu))
    model.add(tf.keras.layers.Dense(units = 1, activation = None))
    return model


# Read data and convert to needed format
def read_dataset(filename, mode, batch_size = 512):
    def _input_fn():
        def decode_csv(row):
            # Row is a string tensor containing the contents of one row
            features = tf.decode_csv(records = row, record_defaults = DEFAULTS)  # string tensor -> list of 50 rank 0 float tensors
            label = features.pop()  # remove last feature and use as label
            features = tf.stack(values = features, axis = 0)  # list of rank 0 tensors -> single rank 1 tensor
            return {TIMESERIES_COL: features}, label

        # Create list of file names that match "glob" pattern (i.e. data_file_*.csv)
        dataset = tf.data.Dataset.list_files(file_pattern = filename)
        # Read in data from files
        dataset = dataset.flat_map(map_func = tf.data.TextLineDataset)
        # Parse text lines as comma-separated values (CSV)
        dataset = dataset.map(map_func = decode_csv)

        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None  # loop indefinitely
            dataset = dataset.shuffle(buffer_size = 10 * batch_size)
        else:
            num_epochs = 1  # end-of-input after this

        dataset = dataset.repeat(count = num_epochs).batch(batch_size = batch_size)
        return dataset.make_one_shot_iterator().get_next()
    return _input_fn


def serving_input_fn():
    feature_placeholders = {
        TIMESERIES_COL: tf.placeholder(dtype = tf.float32, shape = [None, N_INPUTS])
    }

    features = {
        key: tf.expand_dims(input = tensor, axis = -1)
        for key, tensor in feature_placeholders.items()
    }
    features[TIMESERIES_COL] = tf.squeeze(input = features[TIMESERIES_COL], axis = 2)

    return tf.estimator.export.ServingInputReceiver(features = features, receiver_tensors = feature_placeholders)


# Wrapper function to build selected Keras model type
def sequence_regressor(hparams):
    # 1. Run the appropriate model
    model_functions = {
        "linear": linear_model,
        "dnn": dnn_model,
        "cnn": cnn_model,
        "rnn": rnn_model,
        "rnn2": rnn2_model}
    
    # Get function pointer for selected model type
    model_function = model_functions[hparams["model"]]
    
    # Build selected Keras model
    model = model_function(hparams)
    
    return model


def train_and_evaluate(output_dir, hparams):
    tf.summary.FileWriterCache.clear() # ensure filewriter cache is clear for TensorBoard events file
    
    # Build Keras model
    model = sequence_regressor(hparams)
    
    # Compile Keras model with optimizer, loss function, and eval metrics
    model.compile(
        optimizer = "adam",
        loss = "mse",
        metrics = ["mse"])
        
    # Convert Keras model to an Estimator
    estimator = tf.keras.estimator.model_to_estimator(
        keras_model = model, 
        model_dir = output_dir, 
        config = tf.estimator.RunConfig(save_checkpoints_secs = hparams["min_eval_frequency"]))
    
    # Set estimator's train_spec to use train_input_fn and train for so many steps
    train_spec = tf.estimator.TrainSpec(
        input_fn = read_dataset(
            filename = hparams['train_data_path'],
            mode = tf.estimator.ModeKeys.TRAIN,
            batch_size = hparams['train_batch_size']),
        max_steps = hparams['train_steps'])
    
    # Create exporter that uses serving_input_fn to create saved_model for serving
    exporter = tf.estimator.LatestExporter(name = 'exporter', serving_input_receiver_fn = serving_input_fn)
    
    # Set estimator's eval_spec to use eval_input_fn and export saved_model
    eval_spec = tf.estimator.EvalSpec(
        input_fn = read_dataset(
            filename = hparams['eval_data_path'],
            mode = tf.estimator.ModeKeys.EVAL,
            batch_size = 1000),
        steps = None,
        exporters = exporter,
        start_delay_secs = hparams['eval_delay_secs'],
        throttle_secs = hparams['min_eval_frequency'])
    
    # Run train_and_evaluate loop
    tf.estimator.train_and_evaluate(
        estimator = estimator, 
        train_spec = train_spec, 
        eval_spec = eval_spec)