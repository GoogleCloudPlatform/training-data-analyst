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

TIMESERIES_COL = 'height'
N_OUTPUTS = 1  # in each sequence, 1-49 are features, and 50 is label
SEQ_LEN = None
DEFAULTS = None
N_INPUTS = None


def init(hparams):
    global SEQ_LEN, DEFAULTS, N_INPUTS
    SEQ_LEN = hparams['sequence_length']
    DEFAULTS = [[0.0] for x in range(0, SEQ_LEN)]
    N_INPUTS = SEQ_LEN - N_OUTPUTS


def linear_model(features, mode, params):
    X = features[TIMESERIES_COL]
    predictions = tf.layers.dense(X, 1, activation=None)
    return predictions


def dnn_model(features, mode, params):
    X = features[TIMESERIES_COL]
    h1 = tf.layers.dense(X, 10, activation=tf.nn.relu)
    h2 = tf.layers.dense(h1, 3, activation=tf.nn.relu)
    predictions = tf.layers.dense(h2, 1, activation=None)  # linear output: regression
    return predictions


def cnn_model(features, mode, params):
    X = tf.reshape(features[TIMESERIES_COL],
                   [-1, N_INPUTS, 1])  # as a 1D "sequence" with only one time-series observation (height)
    c1 = tf.layers.conv1d(X, filters=N_INPUTS // 2,
                          kernel_size=3, strides=1,
                          padding='same', activation=tf.nn.relu)
    p1 = tf.layers.max_pooling1d(c1, pool_size=2, strides=2)

    c2 = tf.layers.conv1d(p1, filters=N_INPUTS // 2,
                          kernel_size=3, strides=1,
                          padding='same', activation=tf.nn.relu)
    p2 = tf.layers.max_pooling1d(c2, pool_size=2, strides=2)

    outlen = p2.shape[1] * p2.shape[2]
    c2flat = tf.reshape(p2, [-1, outlen])
    h1 = tf.layers.dense(c2flat, 3, activation=tf.nn.relu)
    predictions = tf.layers.dense(h1, 1, activation=None)  # linear output: regression
    return predictions


def rnn_model(features, mode, params):
    CELL_SIZE = N_INPUTS // 3  # size of the internal state in each of the cells

    # 1. dynamic_rnn needs 3D shape: [BATCH_SIZE, N_INPUTS, 1]
    x = tf.reshape(features[TIMESERIES_COL], [-1, N_INPUTS, 1])

    # 2. configure the RNN
    cell = tf.nn.rnn_cell.GRUCell(CELL_SIZE)
    outputs, state = tf.nn.dynamic_rnn(cell, x, dtype=tf.float32)

    # 3. pass rnn output through a dense layer
    h1 = tf.layers.dense(state, N_INPUTS // 2, activation=tf.nn.relu)
    predictions = tf.layers.dense(h1, 1, activation=None)  # (?, 1)
    return predictions


# 2-layer RNN
def rnn2_model(features, mode, params):
    # dynamic_rnn needs 3D shape: [BATCH_SIZE, N_INPUTS, 1]
    x = tf.reshape(features[TIMESERIES_COL], [-1, N_INPUTS, 1])

    # 2. configure the RNN
    cell1 = tf.nn.rnn_cell.GRUCell(N_INPUTS * 2)
    cell2 = tf.nn.rnn_cell.GRUCell(N_INPUTS // 2)
    cells = tf.nn.rnn_cell.MultiRNNCell([cell1, cell2])
    outputs, state = tf.nn.dynamic_rnn(cells, x, dtype=tf.float32)
    # 'state' is now a tuple containing the final state of each cell layer
    # we use state[1] below to extract the final state of the final layer
    
    # 3. pass rnn output through a dense layer
    h1 = tf.layers.dense(state[1], cells.output_size // 2, activation=tf.nn.relu)
    predictions = tf.layers.dense(h1, 1, activation=None)  # (?, 1)
    return predictions


# create N-1 predictions
def rnnN_model(features, mode, params):
    # dynamic_rnn needs 3D shape: [BATCH_SIZE, N_INPUTS, 1]
    x = tf.reshape(features[TIMESERIES_COL], [-1, N_INPUTS, 1])

    # 2. configure the RNN
    cell1 = tf.nn.rnn_cell.GRUCell(N_INPUTS * 2)
    cell2 = tf.nn.rnn_cell.GRUCell(N_INPUTS // 2)
    cells = tf.nn.rnn_cell.MultiRNNCell([cell1, cell2])
    outputs, state = tf.nn.dynamic_rnn(cells, x, dtype=tf.float32)
    # 'outputs' contains the state of the final layer for every time step
    # not just the last time step (?,N_INPUTS, final cell size)
    
    # 3. pass state for each time step through a DNN, to get a prediction
    # for each time step 
    h1 = tf.layers.dense(outputs, cells.output_size, activation=tf.nn.relu)
    h2 = tf.layers.dense(h1, cells.output_size // 2, activation=tf.nn.relu)
    predictions = tf.layers.dense(h2, 1, activation=None)  # (?, N_INPUTS, 1)
    predictions = tf.reshape(predictions, [-1, N_INPUTS])
    return predictions # return prediction for each time step


# read data and convert to needed format
def read_dataset(filename, mode, batch_size=512):
    def _input_fn():
        def decode_csv(row):
            # row is a string tensor containing the contents of one row
            features = tf.decode_csv(row, record_defaults=DEFAULTS)  # string tensor -> list of 50 rank 0 float tensors
            label = features.pop()  # remove last feature and use as label
            features = tf.stack(features)  # list of rank 0 tensors -> single rank 1 tensor
            return {TIMESERIES_COL: features}, label

        # Create list of file names that match "glob" pattern (i.e. data_file_*.csv)
        dataset = tf.data.Dataset.list_files(filename)
        # Read in data from files
        dataset = dataset.flat_map(tf.data.TextLineDataset)
        # Parse text lines as comma-separated values (CSV)
        dataset = dataset.map(decode_csv)

        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None  # loop indefinitely
            dataset = dataset.shuffle(buffer_size=10 * batch_size)
        else:
            num_epochs = 1  # end-of-input after this

        dataset = dataset.repeat(num_epochs).batch(batch_size)
        return dataset.make_one_shot_iterator().get_next()

    return _input_fn


def serving_input_fn():
    feature_placeholders = {
        TIMESERIES_COL: tf.placeholder(tf.float32, [None, N_INPUTS])
    }

    features = {
        key: tf.expand_dims(tensor, -1)
        for key, tensor in feature_placeholders.items()
    }
    features[TIMESERIES_COL] = tf.squeeze(features[TIMESERIES_COL], axis=[2])

    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)


def compute_errors(features, labels, predictions):
    labels = tf.expand_dims(labels, -1)  # rank 1 -> rank 2 to match rank of predictions

    if predictions.shape[1] == 1:
        loss = tf.losses.mean_squared_error(labels, predictions)
        rmse = tf.metrics.root_mean_squared_error(labels, predictions)
        return loss, rmse
    else:
        # one prediction for every input in sequence
        # get 1-N of (x + label)
        labelsN = tf.concat([features[TIMESERIES_COL], labels], axis=1)
        labelsN = labelsN[:, 1:]
        # loss is computed from the last 1/3 of the series
        N = (2 * N_INPUTS) // 3
        loss = tf.losses.mean_squared_error(labelsN[:, N:], predictions[:, N:])
        # rmse is computed from last prediction and last label
        lastPred = predictions[:, -1]
        rmse = tf.metrics.root_mean_squared_error(labels, lastPred)
        return loss, rmse

# RMSE when predicting same as last value
def same_as_last_benchmark(features, labels):
    predictions = features[TIMESERIES_COL][:,-1] # last value in input sequence
    return tf.metrics.root_mean_squared_error(labels, predictions)


# create the inference model
def sequence_regressor(features, labels, mode, params):
    # 1. run the appropriate model
    model_functions = {
        'linear': linear_model,
        'dnn': dnn_model,
        'cnn': cnn_model,
        'rnn': rnn_model,
        'rnn2': rnn2_model,
        'rnnN': rnnN_model}
    model_function = model_functions[params['model']]
    predictions = model_function(features, mode, params)

    # 2. loss function, training/eval ops
    loss = None
    train_op = None
    eval_metric_ops = None
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        loss, rmse = compute_errors(features, labels, predictions)

        if mode == tf.estimator.ModeKeys.TRAIN:
            # this is needed for batch normalization, but has no effect otherwise
            update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(update_ops):
                # 2b. set up training operation
                train_op = tf.contrib.layers.optimize_loss(
                    loss,
                    tf.train.get_global_step(),
                    learning_rate=params['learning_rate'],
                    optimizer="Adam")

        # 2c. eval metric
        eval_metric_ops = {
            "RMSE": rmse,
            "RMSE_same_as_last": same_as_last_benchmark(features, labels),
        }

    # 3. Create predictions
    if predictions.shape[1] != 1:
        predictions = predictions[:, -1]  # last predicted value
    predictions_dict = {"predicted": predictions}

    # 4. return EstimatorSpec
    return tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=predictions_dict,
        loss=loss,
        train_op=train_op,
        eval_metric_ops=eval_metric_ops,
        export_outputs={
            'predictions': tf.estimator.export.PredictOutput(predictions_dict)}
    )


def train_and_evaluate(output_dir, hparams):
    tf.summary.FileWriterCache.clear() # ensure filewriter cache is clear for TensorBoard events file
    get_train = read_dataset(hparams['train_data_path'],
                             tf.estimator.ModeKeys.TRAIN,
                             hparams['train_batch_size'])
    get_valid = read_dataset(hparams['eval_data_path'],
                             tf.estimator.ModeKeys.EVAL,
                             1000)
    estimator = tf.estimator.Estimator(model_fn=sequence_regressor,
                                       params=hparams,
                                       config=tf.estimator.RunConfig(
                                           save_checkpoints_secs=
                                           hparams['min_eval_frequency']),
                                       model_dir=output_dir)
    train_spec = tf.estimator.TrainSpec(input_fn=get_train,
                                        max_steps=hparams['train_steps'])
    exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)
    eval_spec = tf.estimator.EvalSpec(input_fn=get_valid,
                                      steps=None,
                                      exporters=exporter,
                                      start_delay_secs=hparams['eval_delay_secs'],
                                      throttle_secs=hparams['min_eval_frequency'])
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
