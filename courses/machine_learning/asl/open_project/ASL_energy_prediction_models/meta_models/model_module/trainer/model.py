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

import sys
import copy
import tensorflow as tf

# Set logging to be level of INFO
tf.logging.set_verbosity(tf.logging.INFO)

# Determine CSV and label columns
CSV_COLUMNS = 'price,dayofweek,hourofday'.split(',')
LABEL_COLUMN = 'price'

# Set default values for each CSV column
DEFAULTS = [[0.0], [0.0], [0.0]]

# Create an input function reading a file using the Dataset API
# Then provide the results to the Estimator API
def read_dataset(filename, mode, batch_size, params):
    def _input_fn():
        print("\nread_dataset: _input_fn: filename = {}".format(filename))
        print("read_dataset: _input_fn: mode = {}".format(mode))
        print("read_dataset: _input_fn: batch_size = {}".format(batch_size))
        print("read_dataset: _input_fn: params = {}\n".format(params))

        def decode_csv(value_column):
            print("\nread_dataset: _input_fn: decode_csv: value_column = {}".format(value_column))
            columns = tf.decode_csv(records = value_column, record_defaults = DEFAULTS)
            print("read_dataset: _input_fn: decode_csv: columns = {}".format(columns))
            features = dict(zip(CSV_COLUMNS, columns))
            print("read_dataset: _input_fn: decode_csv: features = {}".format(features))
            return features

        def create_sequences(features):
            # This function will create sequences out of the base features and labels by offsetting each sequence by one time step
            print("\nread_dataset: _input_fn: create_sequences: features = {}".format(features))

            # These are our sequence lengths per batch, which is just our input_sequence_length tiled since all of our sequences are the same length
            sequence_lengths = tf.tile(input = [params["input_sequence_length"]], multiples = [params["batch_size"]])
            print("read_dataset: _input_fn: create_sequences: sequence_lengths = {}".format(sequence_lengths))

            # We will slice our label column since we will also be using the earlier values as a feature and the later values as the labels
            label = features[LABEL_COLUMN][params['input_sequence_length'] + params['horizon']:] # shape = (batch_size,)
            print("read_dataset: _input_fn: create_sequences: label = {}".format(label))

            # Now use tf.map_fn to break our labels and features into a params['batch_size'] number of sequences offset by one timestep
            label = tf.map_fn(fn = lambda i: label[i:params['output_sequence_length'] + i], 
                              elems = tf.range(params['batch_size']), dtype=tf.float32) # shape = (params['batch_size'], params['input_sequence_length'])
            print("read_dataset: _input_fn: create_sequences: label = {}".format(label))

            for key,val in features.items():
                features[key] = tf.map_fn(fn = lambda i: features[key][i:params['input_sequence_length'] + i], 
                                          elems = tf.range(params['batch_size']), dtype=tf.float32) # shape = (params['batch_size'], params['input_sequence_length'])
                print("read_dataset: _input_fn: create_sequences: features[{}] = {}".format(key, features[key]))

                # Reversing the input sequence can often improve performance because it shortens the path from the decoder to the relevant parts of the encoder
                if params["reverse_sequence"] == True:
                    features[key] = tf.reverse_sequence(input = features[key], seq_lengths = sequence_lengths, seq_axis = 1, batch_axis = 0)
                    print("read_dataset: _input_fn: create_sequences: reversed features[{}] = {}".format(key, features[key]))

            # Return our dictionary of feature tensors and our label tensor
            return features, label

        # Create list of files that match pattern
        file_list = tf.gfile.Glob(filename = filename)
        print("\nread_dataset: _input_fn: file_list = {}".format(file_list))

        # Create dataset from file list
        dataset = tf.data.TextLineDataset(filenames = file_list)  # Read text file
        print("read_dataset: _input_fn: dataset.TextLineDataset(file_list) = {}".format(dataset))

        # Decode the CSV file into a features dictionary of tensors and a labels tensor
        dataset = dataset.map(map_func = decode_csv)
        print("read_dataset: _input_fn: dataset.map(decode_csv) = {}".format(dataset))

        # Determine amount of times to repeat file based on if we are training or evaluating
        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None # indefinitely
        else:
            num_epochs = 1 # end-of-input after this

        # Repeat files num_epoch times
        dataset = dataset.repeat(count = num_epochs)
        print("read_dataset: _input_fn: dataset.repeat(num_epochs) = {}".format(dataset))

        # Group the data into batches
        dataset = dataset.apply(transformation_func = tf.contrib.data.batch_and_drop_remainder(batch_size = batch_size))
        print("read_dataset: _input_fn: dataset.batch(batch_size) = {}".format(dataset))

        # Create sequences out of our batched data
        dataset = dataset.map(map_func = create_sequences)
        print("read_dataset: _input_fn: dataset.map(create_sequences) = {}".format(dataset))

        # Determine if we should shuffle based on if we are training or evaluating
        if mode == tf.estimator.ModeKeys.TRAIN:
            dataset = dataset.shuffle(buffer_size = 10 * batch_size)
            print("read_dataset: _input_fn: dataset.shuffle(buffer_size = 10 * batch_size) = {}".format(dataset))

        # Create a iterator and then pull the next batch of features and labels from the example queue
        batch_features, batch_labels = dataset.make_one_shot_iterator().get_next()
        print("read_dataset: _input_fn: batch_features = {}".format(batch_features))
        print("read_dataset: _input_fn: batch_labels = {}\n".format(batch_labels))

        return batch_features, batch_labels
    return _input_fn

# Create our model function to be used in our custom estimator
def dnn_regression(features, labels, mode, params):
    print("\ndnn_regression: features = {}".format(features))
    print("dnn_regression: labels = {}".format(labels))
    print("dnn_regression: mode = {}".format(mode))
    print("dnn_regression: params = {}".format(params))

    # 0. Get tensor into correct shape
    # Get dynamic batch size
    current_batch_size = tf.shape(features["price"])[0]
    print("dnn_regression: current_batch_size = {}".format(current_batch_size))

    # Get the number of features 
    number_of_features = len(features)
    print("dnn_regression: number_of_features = {}".format(number_of_features))

    # Stack all of the features into a 3-D tensor
    X = tf.stack(features.values(), axis = 2) # shape = (batch_size, input_sequence_length, number_of_features)
    print("dnn_regression: X = {}".format(X))

    # For DNN I want to flatten everything
    X_flattened = tf.reshape(X, [current_batch_size, params['input_sequence_length'] * number_of_features]) # shape = (batch_size, input_sequence_length * number_of_features)
    print("dnn_regression: X_flattened = {}".format(X_flattened))

    # 1. Create the DNN structure now
    # Create the input layer to our frame DNN
    network = X_flattened # shape = (batch_size, input_sequence_length * number_of_features)
    print("dnn_regression: network = {}".format(network))

    # Add hidden layers with the given number of units/neurons per layer
    for units in params['dnn_hidden_units']:
        network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size, dnn_hidden_units[i])
        print("dnn_regression: network = {}, units = {}".format(network, units))

    # Connect the final hidden layer to a dense layer with no activation to get the predictions
    predictions = tf.layers.dense(inputs = network, units = params['output_sequence_length'], activation = None) # shape = (current_batch_size, output_sequence_length)
    print("dnn_regression: predictions = {}\n".format(predictions))

    # 2. Loss function, training/eval ops
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        loss = tf.losses.mean_squared_error(labels = labels, predictions = predictions)
        train_op = tf.contrib.layers.optimize_loss(
            loss = loss,
            global_step = tf.train.get_global_step(),
            learning_rate = params['learning_rate'],
            optimizer = "Adam")
        eval_metric_ops = {
            "rmse": tf.metrics.root_mean_squared_error(labels = labels, predictions = predictions),
            "mae": tf.metrics.mean_absolute_error(labels = labels, predictions = predictions)
        }
    else:
        loss = None
        train_op = None
        eval_metric_ops = None

    # 3. Create predictions
    predictions_dict = {"predicted": predictions}

    # 4. Create export outputs
    export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs = predictions)}

    # 5. Return EstimatorSpec
    return tf.estimator.EstimatorSpec(
        mode = mode,
        predictions = predictions_dict,
        loss = loss,
        train_op = train_op,
        eval_metric_ops = eval_metric_ops,
        export_outputs = export_outputs)

# Create our model function to be used in our custom estimator
def stacked_lstm_regression(features, labels, mode, params):
    print("\nstacked_lstm_regression: features = {}".format(features))
    print("stacked_lstm_regression: labels = {}".format(labels))
    print("stacked_lstm_regression: mode = {}".format(mode))
    print("stacked_lstm_regression: params = {}".format(params))

    # 0. Get tensor into correct shape
    # Get dynamic batch size
    current_batch_size = tf.shape(features["price"])[0]
    print("stacked_lstm_regression: current_batch_size = {}".format(current_batch_size))

    # Get the number of features 
    number_of_features = len(features)
    print("stacked_lstm_regression: number_of_features = {}".format(number_of_features))

    # Stack all of the features into a 3-D tensor
    X = tf.stack(values = features.values(), axis = 2) # shape = (current_batch_size, input_sequence_length, number_of_features)
    print("stacked_lstm_regression: X = {}".format(X))

    # Unstack all of 3-D features tensor into a sequence(list) of 2-D tensors of shape = (current_batch_size, number_of_features)
    X_sequence = tf.unstack(value = X, num = params['input_sequence_length'], axis = 1)
    print("stacked_lstm_regression: X_sequence = {}".format(X_sequence))

    # 1. Configure the RNN
    # First create a list of LSTM cells using our list of lstm hidden unit sizes
    lstm_cells = [tf.contrib.rnn.BasicLSTMCell(num_units = units, forget_bias = 1.0, state_is_tuple = True) for units in params["lstm_hidden_units"]] # list of LSTM cells
    print("stacked_lstm_regression: lstm_cells = {}".format(lstm_cells))

    # Next apply a dropout wrapper to our stack of LSTM cells, in this case just on the outputs
    dropout_lstm_cells = [tf.nn.rnn_cell.DropoutWrapper(cell = lstm_cells[cell_index], 
                                                        input_keep_prob = 1.0, 
                                                        output_keep_prob = params["lstm_dropout_output_keep_probs"][cell_index], 
                                                        state_keep_prob = 1.0) for cell_index in range(len(lstm_cells))]
    print("stacked_lstm_regression: dropout_lstm_cells = {}".format(dropout_lstm_cells))

    # Create a stack of layers of LSTM cells
    stacked_lstm_cells = tf.contrib.rnn.MultiRNNCell(cells = dropout_lstm_cells, state_is_tuple = True) # combines list into MultiRNNCell object
    print("stacked_lstm_regression: stacked_lstm_cells = {}".format(stacked_lstm_cells))

    # Create a static RNN where we will keep a list of all of the intermediate hidden state outputs
    outputs, _ = tf.nn.static_rnn(cell = stacked_lstm_cells, # creates list input_sequence_length elements long of 2-D tensors of shape = (current_batch_size, lstm_hidden_units[-1])
                                  inputs = X_sequence, 
                                  initial_state = stacked_lstm_cells.zero_state(batch_size = current_batch_size, dtype = tf.float32), 
                                  dtype = tf.float32)
    print("stacked_lstm_regression: outputs = {}".format(outputs))

    # Slice outputs to keep only the last cell of the RNN
    last_output = outputs[-1] # shape = (current_batch_size, lstm_hidden_units[-1])
    print("stacked_lstm_regression: last_output = {}".format(last_output))

    # 2. Create the DNN structure now
    # Create the input layer to our DNN
    network = last_output # shape = (current_batch_size, lstm_hidden_units[-1])
    print("stacked_lstm_regression: network = {}".format(network))

    # Add hidden layers with the given number of units/neurons per layer
    for units in params['dnn_hidden_units']:
        network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size, dnn_hidden_units[i])
        print("stacked_lstm_regression: network = {}, units = {}".format(network, units))

    # Connect the final hidden layer to a dense layer with no activation to get the predictions
    predictions = tf.layers.dense(inputs = network, units = params['output_sequence_length'], activation = None) # shape = (current_batch_size, output_sequence_length)
    print("stacked_lstm_regression: predictions = {}\n".format(predictions))

    # 3. Loss function, training/eval ops
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        loss = tf.losses.mean_squared_error(labels = labels, predictions = predictions)
        train_op = tf.contrib.layers.optimize_loss(
            loss = loss,
            global_step = tf.train.get_global_step(),
            learning_rate = params['learning_rate'],
            optimizer = "Adam")
        eval_metric_ops = {
            "rmse": tf.metrics.root_mean_squared_error(labels = labels, predictions = predictions),
            "mae": tf.metrics.mean_absolute_error(labels = labels, predictions = predictions)
        }
    else:
        loss = None
        train_op = None
        eval_metric_ops = None

    # 4. Create predictions
    predictions_dict = {"predicted": predictions}

    # 5. Create export outputs
    export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs = predictions)}

    # 6. Return EstimatorSpec
    return tf.estimator.EstimatorSpec(
        mode = mode,
        predictions = predictions_dict,
        loss = loss,
        train_op = train_op,
        eval_metric_ops = eval_metric_ops,
        export_outputs = export_outputs)

# Create our model function to be used in our custom estimator
def stacked_lstmN_regression(features, labels, mode, params):
    print("\nstacked_lstmN_regression: features = {}".format(features))
    print("stacked_lstmN_regression: labels = {}".format(labels))
    print("stacked_lstmN_regression: mode = {}".format(mode))
    print("stacked_lstmN_regression: params = {}".format(params))

    # 0. Get tensor into correct shape
    # Get dynamic batch size
    current_batch_size = tf.shape(features["price"])[0]
    print("stacked_lstmN_regression: current_batch_size = {}".format(current_batch_size))

    # Get the number of features 
    number_of_features = len(features)
    print("stacked_lstmN_regression: number_of_features = {}".format(number_of_features))

    # Stack all of the features into a 3-D tensor
    X = tf.stack(values = features.values(), axis = 2) # shape = (current_batch_size, input_sequence_length, number_of_features)
    print("stacked_lstmN_regression: X = {}".format(X))

    # Unstack all of 3-D features tensor into a sequence(list) of 2-D tensors of shape = (current_batch_size, number_of_features)
    X_sequence = tf.unstack(value = X, num = params['input_sequence_length'], axis = 1)
    print("stacked_lstmN_regression: X_sequence = {}".format(X_sequence))

    # 1. Configure the RNN
    # First create a list of LSTM cells using our list of lstm hidden unit sizes
    lstm_cells = [tf.contrib.rnn.BasicLSTMCell(num_units = units, forget_bias = 1.0, state_is_tuple = True) for units in params["lstm_hidden_units"]] # list of LSTM cells
    print("stacked_lstmN_regression: lstm_cells = {}".format(lstm_cells))

    # Next apply a dropout wrapper to our stack of LSTM cells, in this case just on the outputs
    dropout_lstm_cells = [tf.nn.rnn_cell.DropoutWrapper(cell = lstm_cells[cell_index], 
                                                        input_keep_prob = 1.0, 
                                                        output_keep_prob = params["lstm_dropout_output_keep_probs"][cell_index], 
                                                        state_keep_prob = 1.0) for cell_index in range(len(lstm_cells))]
    print("stacked_lstmN_regression: dropout_lstm_cells = {}".format(dropout_lstm_cells))

    # Create a stack of layers of LSTM cells
    stacked_lstm_cells = tf.contrib.rnn.MultiRNNCell(cells = dropout_lstm_cells, state_is_tuple = True) # combines list into MultiRNNCell object
    print("stacked_lstmN_regression: stacked_lstm_cells = {}".format(stacked_lstm_cells))

    # Create a static RNN where we will keep a list of all of the intermediate hidden state outputs
    outputs, _ = tf.nn.static_rnn(cell = stacked_lstm_cells, # creates list input_sequence_length elements long of 2-D tensors of shape = (current_batch_size, lstm_hidden_units[-1])
                                  inputs = X_sequence, 
                                  initial_state = stacked_lstm_cells.zero_state(batch_size = current_batch_size, dtype = tf.float32), 
                                  dtype = tf.float32)
    print("stacked_lstmN_regression: outputs = {}".format(outputs))

    # Stack all of outputs into a 3-D tensor
    stacked_outputs = tf.stack(values = outputs, axis = 1) # shape = (current_batch_size, input_sequence_length, lstm_hidden_units[-1])
    print("stacked_lstmN_regression: stacked_outputs = {}".format(stacked_outputs))

    # Flatten stacked outputs into a 2-D tensor
    flattened_stacked_outputs = tf.reshape(tensor = stacked_outputs, shape = [current_batch_size, params['input_sequence_length'] * params['lstm_hidden_units'][-1]]) # shape = (current_batch_size, input_sequence_length * lstm_hidden_units[-1])
    print("stacked_lstmN_regression: flattened_stacked_outputs = {}".format(flattened_stacked_outputs))

    # 2. Create the DNN structure now
    # Create the input layer to our DNN
    network = flattened_stacked_outputs # shape = (current_batch_size, input_sequence_length * lstm_hidden_units[-1])
    print("stacked_lstmN_regression: network = {}".format(network))

    # Add hidden layers with the given number of units/neurons per layer
    for units in params['dnn_hidden_units']:
        network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size, dnn_hidden_units[i])
        print("stacked_lstmN_regression: network = {}, units = {}".format(network, units))

    # Connect the final hidden layer to a dense layer with no activation to get the predictions
    predictions = tf.layers.dense(inputs = network, units = params['output_sequence_length'], activation = None) # shape = (current_batch_size, output_sequence_length)
    print("stacked_lstmN_regression: predictions = {}\n".format(predictions))

    # 3. Loss function, training/eval ops
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        loss = tf.losses.mean_squared_error(labels = labels, predictions = predictions)
        train_op = tf.contrib.layers.optimize_loss(
            loss = loss,
            global_step = tf.train.get_global_step(),
            learning_rate = params['learning_rate'],
            optimizer = "Adam")
        eval_metric_ops = {
            "rmse": tf.metrics.root_mean_squared_error(labels = labels, predictions = predictions),
            "mae": tf.metrics.mean_absolute_error(labels = labels, predictions = predictions)
        }
    else:
        loss = None
        train_op = None
        eval_metric_ops = None

    # 4. Create predictions
    predictions_dict = {"predicted": predictions}

    # 5. Create export outputs
    export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs = predictions)}

    # 6. Return EstimatorSpec
    return tf.estimator.EstimatorSpec(
        mode = mode,
        predictions = predictions_dict,
        loss = loss,
        train_op = train_op,
        eval_metric_ops = eval_metric_ops,
        export_outputs = export_outputs)

# Create our model function to be used in our custom estimator
def encoder_decoder_stacked_lstm_regression(features, labels, mode, params):
    print("\nencoder_decoder_stacked_lstm_regression: features = {}".format(features))
    print("encoder_decoder_stacked_lstm_regression: labels = {}".format(labels)) # shape = (current_batch_size, output_sequence_length)
    print("encoder_decoder_stacked_lstm_regression: mode = {}".format(mode))
    print("encoder_decoder_stacked_lstm_regression: params = {}".format(params))

    # 0. Get input sequence tensor into correct shape
    # Get dynamic batch size in case there was a partially filled batch
    current_batch_size = tf.shape(features["price"])[0]
    print("encoder_decoder_stacked_lstm_regression: current_batch_size = {}".format(current_batch_size))

    # Get the number of features 
    number_of_features = len(features)
    print("encoder_decoder_stacked_lstm_regression: number_of_features = {}".format(number_of_features))

    # Stack all of the features into a 3-D tensor
    X = tf.stack(values = features.values(), axis = 2) # shape = (current_batch_size, input_sequence_length, number_of_features)
    print("encoder_decoder_stacked_lstm_regression: X = {}".format(X))

    # Unstack all of 3-D features tensor into a sequence(list) of 2-D tensors of shape = (current_batch_size, number_of_features)
    X_sequence = tf.unstack(value = X, num = params['input_sequence_length'], axis = 1)
    print("encoder_decoder_stacked_lstm_regression: X_sequence = {}".format(X_sequence))

    ################################################################################

    # 1. Create encoder of encoder-decoder LSTM stacks
    # First create a list of LSTM cells using our list of lstm hidden unit sizes
    lstm_cells = [tf.contrib.rnn.BasicLSTMCell(num_units = units, forget_bias = 1.0, state_is_tuple = True) for units in params["lstm_hidden_units"]] # list of LSTM cells
    print("encoder_decoder_stacked_lstm_regression: lstm_cells = {}".format(lstm_cells))

    # Next apply a dropout wrapper to our stack of LSTM cells, in this case just on the outputs
    dropout_lstm_cells = [tf.nn.rnn_cell.DropoutWrapper(cell = lstm_cells[cell_index], 
                                                        input_keep_prob = 1.0, 
                                                        output_keep_prob = params["lstm_dropout_output_keep_probs"][cell_index], 
                                                        state_keep_prob = 1.0) for cell_index in range(len(lstm_cells))]
    print("encoder_decoder_stacked_lstm_regression: dropout_lstm_cells = {}".format(dropout_lstm_cells))

    # Create a stack of layers of LSTM cells
    stacked_lstm_cells = tf.contrib.rnn.MultiRNNCell(cells = dropout_lstm_cells, state_is_tuple = True) # combines list into MultiRNNCell object
    print("encoder_decoder_stacked_lstm_regression: stacked_lstm_cells = {}".format(stacked_lstm_cells))

    # Create the encoder variable scope
    with tf.variable_scope("encoder"):
        # Clone the stacked_lstm_cells subgraph since we will be using a copy for the encoder side and the decoder side
        encoder_cells = copy.deepcopy(stacked_lstm_cells)
        print("encoder_decoder_stacked_lstm_regression: encoder_cells = {}".format(encoder_cells))

        # Encode the input sequence using our encoder stack of LSTMs
        encoder_outputs, encoder_final_state = tf.nn.static_rnn(cell = encoder_cells, inputs = X_sequence, dtype = tf.float32)
        print("encoder_decoder_stacked_lstm_regression: encoder_outputs = {}".format(encoder_outputs)) # list input_sequence_length long of shape = (current_batch_size, lstm_hidden_units[-1])
        print("encoder_decoder_stacked_lstm_regression: encoder_final_state = {}".format(encoder_final_state)) # tuple of final encoder c_state and h_state

  ################################################################################

    # 2. Create decoder of encoder-decoder LSTM stacks
    # The rnn_decoder function takes labels during TRAIN/EVAL and a start token followed by its previous predictions during PREDICT
    # Starts with an intial state of the final encoder states
    def rnn_decoder(decoder_inputs, initial_state, cell, inference):
        # Create the decoder variable scope
        with tf.variable_scope("decoder"):
            # Load in our initial state from our encoder
            state = initial_state # tuple of final encoder c_state and h_state
            print("encoder_decoder_stacked_lstm_regression: rnn_decoder: state = {}".format(state))

            # Create an empty list to store our hidden state output for every timestep
            outputs = []

            # Begin with no previous output
            previous_output = None

            # Loop over all of our decoder_inputs which will be output_sequence_length long
            for index, decoder_input in enumerate(decoder_inputs):
                # If there has been a previous output then we will determine the next input
                if previous_output is not None:
                    # Create the input layer to our DNN
                    network = previous_output # shape = (current_batch_size, lstm_hidden_units[-1])
                    print("encoder_decoder_stacked_lstm_regression: rnn_decoder: network = {}".format(network))

                    # Create our dnn variable scope
                    with tf.variable_scope(name_or_scope = "dnn", reuse = tf.AUTO_REUSE):
                        # Add hidden layers with the given number of units/neurons per layer
                        for units in params['dnn_hidden_units']:
                            network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size, dnn_hidden_units[i])
                            print("encoder_decoder_stacked_lstm_regression: rnn_decoder: network = {}, units = {}".format(network, units))
              
                        # Connect the final hidden layer to a dense layer with no activation to get the logits
                        logits = tf.layers.dense(inputs = network, units = 1, activation = None) # shape = (current_batch_size, 1)
                        print("encoder_decoder_stacked_lstm_regression: rnn_decoder: logits = {}\n".format(logits))
          
                    # If we are in inference then we will overwrite our next decoder_input with the logits we just calculated.
                    # Otherwise, we leave the decoder_input input as it was from the enumerated list
                    # We have to calculate the logits even when not using them so that the correct dnn subgraph will be generated here and after the encoder-decoder for both training and inference
                    if inference == True:
                        decoder_input = logits # shape = (current_batch_size, 1)

                    print("encoder_decoder_stacked_lstm_regression: rnn_decoder: decoder_input = {}\n".format(decoder_input))
        
                # If this isn't our first time through the loop, just reuse(share) the same variables for each iteration within the current variable scope
                if index > 0:
                    tf.get_variable_scope().reuse_variables()

                # Run the decoder input through the decoder stack picking up from the previous state
                output, state = cell(decoder_input, state)
                print("encoder_decoder_stacked_lstm_regression: rnn_decoder: output = {}".format(output)) # shape = (current_batch_size, lstm_hidden_units[-1])
                print("encoder_decoder_stacked_lstm_regression: rnn_decoder: state = {}".format(state)) # tuple of final decoder c_state and h_state

                # Append the current decoder hidden state output to the outputs list
                outputs.append(output) # growing list eventually output_sequence_length long of shape = (current_batch_size, lstm_hidden_units[-1])

                # Set the previous output to the output just calculated
                previous_output = output # shape = (current_batch_size, lstm_hidden_units[-1])
            return outputs, state
  
    # Encoder-decoders work differently during training/evaluation and inference so we will have two separate subgraphs for each
    if mode == tf.estimator.ModeKeys.TRAIN  or mode == tf.estimator.ModeKeys.EVAL:
        # Break 2-D labels tensor into a list of 1-D tensors
        unstacked_labels = tf.unstack(value = labels, num = params['output_sequence_length'], axis = 1) # list of output_sequence_length long of shape = (current_batch_size,)
        print("encoder_decoder_stacked_lstm_regression: unstacked_labels = {}".format(unstacked_labels))

        # Expand each 1-D label tensor back into a 2-D tensor
        expanded_unstacked_labels = [tf.expand_dims(input = tensor, axis = -1) for tensor in unstacked_labels] # list of output_sequence_length long of shape = (current_batch_size, 1)
        print("encoder_decoder_stacked_lstm_regression: expanded_unstacked_labels = {}".format(expanded_unstacked_labels))

        # Call our decoder using the labels as our inputs, the encoder final state as our initial state, our other LSTM stack as our cells, and inference set to false
        decoder_outputs, decoder_states = rnn_decoder(decoder_inputs = expanded_unstacked_labels, initial_state = encoder_final_state, cell = stacked_lstm_cells, inference = False)
    else:
        # Since this is inference create fake labels. The list length needs to be the output sequence length even though only the first element is actually used (as our go signal)
        fake_labels = [tf.zeros(shape = [current_batch_size, 1]) for _ in range(params['output_sequence_length'])]
        print("encoder_decoder_stacked_lstm_regression: fake_labels = {}".format(fake_labels))

        # Call our decoder using fake labels as our inputs, the encoder final state as our initial state, our other LSTM stack as our cells, and inference set to true
        decoder_outputs, decoder_states = rnn_decoder(decoder_inputs = fake_labels, initial_state = encoder_final_state, cell = stacked_lstm_cells, inference = True)
    print("encoder_decoder_stacked_lstm_regression: decoder_outputs = {}".format(decoder_outputs)) # list output_sequence_length long of shape = (current_batch_size, lstm_hidden_units[-1])
    print("encoder_decoder_stacked_lstm_regression: decoder_states = {}".format(decoder_states)) # tuple of final decoder c_state and h_state

    # Stack together the list of decoder output tensors into one 
    stacked_decoder_outputs = tf.stack(values = decoder_outputs, axis = 0) # shape = (current_batch_size * output_sequence_length, lstm_hidden_units[-1])
    print("encoder_decoder_stacked_lstm_regression: stacked_decoder_outputs = {}".format(stacked_decoder_outputs))

    ################################################################################

    # 3. Create the DNN structure now after the encoder-decoder LSTM stack
    # Create the input layer to our DNN
    network = stacked_decoder_outputs # shape = (current_batch_size * output_sequence_length, lstm_hidden_units[-1])
    print("encoder_decoder_stacked_lstm_regression: network = {}".format(network))

    # Reuse the same variable scope as we used within our decoder (for inference)
    with tf.variable_scope(name_or_scope = "dnn", reuse = tf.AUTO_REUSE):
        # Add hidden layers with the given number of units/neurons per layer
        for units in params['dnn_hidden_units']:
            network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size * output_sequence_length, dnn_hidden_units[i])
            print("encoder_decoder_stacked_lstm_regression: network = {}, units = {}".format(network, units))

        # Connect the final hidden layer to a dense layer with no activation to get the logits
        logits = tf.layers.dense(inputs = network, units = 1, activation = None) # shape = (current_batch_size * output_sequence_length, 1)
        print("encoder_decoder_stacked_lstm_regression: logits = {}\n".format(logits))
  
    # Now that we are through the final DNN for each sequence element for each example in the batch, reshape the predictions to match our labels
    predictions = tf.reshape(tensor = logits, shape = [current_batch_size, params['output_sequence_length']]) # shape = (current_batch_size, output_sequence_length)
    print("encoder_decoder_stacked_lstm_regression: predictions = {}\n".format(predictions))

    # 3. Loss function, training/eval ops
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        loss = tf.losses.mean_squared_error(labels = labels, predictions = predictions)
        train_op = tf.contrib.layers.optimize_loss(
            loss = loss,
            global_step = tf.train.get_global_step(),
            learning_rate = params['learning_rate'],
            optimizer = "Adam")
        eval_metric_ops = {
            "rmse": tf.metrics.root_mean_squared_error(labels = labels, predictions = predictions),
            "mae": tf.metrics.mean_absolute_error(labels = labels, predictions = predictions)
        }
    else:
        loss = None
        train_op = None
        eval_metric_ops = None

    # 4. Create predictions
    predictions_dict = {"predicted": predictions}

    # 5. Create export outputs
    export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs = predictions)}

    # 6. Return EstimatorSpec
    return tf.estimator.EstimatorSpec(
        mode = mode,
        predictions = predictions_dict,
        loss = loss,
        train_op = train_op,
        eval_metric_ops = eval_metric_ops,
        export_outputs = export_outputs)

# Create our serving input function to accept the data at serving and send it in the right format to our custom estimator
def serving_input_fn(input_sequence_length, reverse_sequence):
    # This function fixes the shape and type of our input strings
    def fix_shape_and_type_for_serving(placeholder):
        # String split each string in the batch and output the values from the resulting SparseTensors
        split_string = tf.map_fn(
            fn = lambda x: tf.string_split(source = [placeholder[x]], delimiter=',').values, 
            elems = tf.range(start = 0, limit = tf.shape(input = placeholder)[0]), 
            dtype = tf.string) # shape = (batch_size, input_sequence_length)
        print("serving_input_fn: fix_shape_and_type_for_serving: split_string = {}".format(split_string))

        # Convert each string in the split tensor to float
        feature_tensor = tf.string_to_number(string_tensor = split_string, out_type = tf.float32) # shape = (batch_size, input_sequence_length)
        print("serving_input_fn: fix_shape_and_type_for_serving: feature_tensor = {}".format(feature_tensor))
        return feature_tensor

    # This function fixes dynamic shape ambiguity of last dimension so that we will be able to use it in our DNN (since tf.layers.dense require the last dimension to be known)
    def get_shape_and_set_modified_shape_2D(tensor, additional_dimension_sizes):
        # Get static shape for tensor and convert it to list
        shape = tensor.get_shape().as_list()
        # Set outer shape to additional_dimension_sizes[0] since we know that this is the correct size
        shape[1] = additional_dimension_sizes[0]
        # Set the shape of tensor to our modified shape
        tensor.set_shape(shape = shape) # shape = (batch_size, additional_dimension_sizes[0])
        print("serving_input_fn: get_shape_and_set_modified_shape_2D: tensor = {}, additional_dimension_sizes = {}".format(tensor, additional_dimension_sizes))
        return tensor

    # Create placeholders to accept the data sent to the model at serving time
    feature_placeholders = { # all features come in as a batch of strings, shape = (batch_size,), this was so because of passing the arrays to online ml-engine prediction
        'price': tf.placeholder(dtype = tf.string, shape = [None]),
        'dayofweek': tf.placeholder(dtype = tf.string, shape = [None]),
        'hourofday': tf.placeholder(dtype = tf.string, shape = [None])
    }
    print("\nserving_input_fn: feature_placeholders = {}".format(feature_placeholders))

    # Create feature tensors
    features = {key: fix_shape_and_type_for_serving(placeholder = tensor) for key, tensor in feature_placeholders.items()}
    print("serving_input_fn: features = {}".format(features))

    # Fix dynamic shape ambiguity of feature tensors for our DNN
    features = {key: get_shape_and_set_modified_shape_2D(tensor = tensor, additional_dimension_sizes = [input_sequence_length]) for key, tensor in features.items()}
    print("serving_input_fn: features = {}".format(features))

    # These are our sequence lengths per batch, which is just our input_sequence_length tiled since all of our sequences are the same length
    sequence_lengths = tf.tile(input = [input_sequence_length], multiples = [tf.shape(feature_placeholders["price"])[0]])
    print("serving_input_fn: sequence_lengths = {}".format(sequence_lengths))

    # Reversing the input sequence can often improve performance because it shortens the path from the decoder to the relevant parts of the encoder
    if reverse_sequence == True:
        features = {key: tf.reverse_sequence(input = tensor, seq_lengths = sequence_lengths, seq_axis = 1, batch_axis = 0) for key, tensor in features.items()}
    else:
        features = {key: tensor for key, tensor in features.items()}
    print("serving_input_fn: features = {}\n".format(features))
        
    return tf.estimator.export.ServingInputReceiver(features = features, receiver_tensors = feature_placeholders)

# Create estimator to train and evaluate
def train_and_evaluate(args):
    # Create our custome estimator using our model function
    estimator = tf.estimator.Estimator(
        model_fn = getattr(sys.modules[__name__], args["model_fn_name"]), # finds within current module the model function based on passed string
        model_dir = args['output_dir'],
        params = {
            "batch_size": args['batch_size'], 
            "input_sequence_length": args["input_sequence_length"], 
            "output_sequence_length": args["output_sequence_length"], 
            "lstm_hidden_units": args["lstm_hidden_units"], 
            "lstm_dropout_output_keep_probs": args["lstm_dropout_output_keep_probs"], 
            "dnn_hidden_units": args["dnn_hidden_units"], 
            "learning_rate": args['learning_rate']})
    # Create train spec to read in our training data
    train_spec = tf.estimator.TrainSpec(
        input_fn = read_dataset(
            filename = args['train_file_pattern'], 
            mode = tf.estimator.ModeKeys.TRAIN, 
            batch_size = args['batch_size'] + args['input_sequence_length'] + args['horizon'] + args['output_sequence_length'] - 1,
            params = args),
        max_steps = args['train_steps'])
    # Create exporter to save out the complete model to disk
    exporter = tf.estimator.LatestExporter(
        name = 'exporter', 
        serving_input_receiver_fn = lambda: serving_input_fn(input_sequence_length = args["input_sequence_length"], reverse_sequence = args["reverse_sequence"]))
    # Create eval spec to read in our validation data and export our model
    eval_spec = tf.estimator.EvalSpec(
        input_fn = read_dataset(
            filename = args['eval_file_pattern'], 
            mode = tf.estimator.ModeKeys.EVAL, 
            batch_size = args['batch_size'] + args['input_sequence_length'] + args['horizon'] + args['output_sequence_length'] - 1,
            params = args),
        steps = None,
        start_delay_secs = args["start_delay_secs"], # start evaluating after N seconds
        throttle_secs = args["throttle_secs"],  # evaluate every N seconds
        exporters = exporter)
    # Create train and evaluate loop to train and evaluate our estimator
    tf.estimator.train_and_evaluate(estimator = estimator, train_spec = train_spec, eval_spec = eval_spec)