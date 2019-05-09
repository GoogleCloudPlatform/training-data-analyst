import tensorflow as tf

# Set logging to be level of INFO
tf.logging.set_verbosity(tf.logging.INFO)

# Determine CSV and label columns
number_of_tags = 5
tag_columns = ["tag_{0}".format(tag) for tag in range(0, number_of_tags)]
UNLABELED_CSV_COLUMNS = tag_columns

LABEL_COLUMN = "anomalous_sequence_flag"
LABELED_CSV_COLUMNS = UNLABELED_CSV_COLUMNS + [LABEL_COLUMN]

# Set default values for each CSV column
UNLABELED_DEFAULTS = [[""] for _ in UNLABELED_CSV_COLUMNS]

LABELED_DEFAULTS = UNLABELED_DEFAULTS + [[0.0]]

# Create an input function reading a file using the Dataset API
# Then provide the results to the Estimator API
def read_dataset(filename, mode, batch_size, params):
    def _input_fn():
        def decode_csv(value_column, sequence_length):
            def convert_sequences_from_strings_to_floats(features, column_list):
                def split_and_convert_string(string_tensor):
                    # Split string tensor into a sparse tensor based on delimiter
                    split_string = tf.string_split(source = tf.expand_dims(input = string_tensor, axis = 0), delimiter = ",")

                    # Converts the values of the sparse tensor to floats
                    converted_tensor = tf.string_to_number(split_string.values, out_type = tf.float64)

                    # Create a new sparse tensor with the new converted values, because the original sparse tensor values are immutable
                    new_sparse_tensor = tf.SparseTensor(indices = split_string.indices, values = converted_tensor, dense_shape = split_string.dense_shape)

                    # Create a dense tensor of the float values that were converted from text csv
                    dense_floats = tf.sparse_tensor_to_dense(sp_input = new_sparse_tensor, default_value = 0.0)

                    dense_floats_vector = tf.squeeze(input = dense_floats, axis = 0)

                    return dense_floats_vector
                    
                for column in column_list:
                    features[column] = split_and_convert_string(features[column])
                    features[column].set_shape([sequence_length])


                return features
                
            if mode == tf.estimator.ModeKeys.TRAIN or (mode == tf.estimator.ModeKeys.EVAL and params["evaluation_mode"] != "tune_anomaly_thresholds"):
                columns = tf.decode_csv(records = value_column, record_defaults = UNLABELED_DEFAULTS, field_delim = ";")
                features = dict(zip(UNLABELED_CSV_COLUMNS, columns))
                features = convert_sequences_from_strings_to_floats(features, UNLABELED_CSV_COLUMNS)
                return features
            else:
                columns = tf.decode_csv(records = value_column, record_defaults = LABELED_DEFAULTS, field_delim = ";")
                features = dict(zip(LABELED_CSV_COLUMNS, columns))
                labels = tf.cast(x = features.pop(LABEL_COLUMN), dtype = tf.float64)
                features = convert_sequences_from_strings_to_floats(features, LABELED_CSV_COLUMNS[0:-1])
                return features, labels
        
        # Create list of files that match pattern
        file_list = tf.gfile.Glob(filename = filename)

        # Create dataset from file list
        dataset = tf.data.TextLineDataset(filenames = file_list)    # Read text file

        # Decode the CSV file into a features dictionary of tensors
        dataset = dataset.map(map_func = lambda x: decode_csv(x, params["sequence_length"]))
        
        # Determine amount of times to repeat file based on if we are training or evaluating
        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None # indefinitely
        else:
            num_epochs = 1 # end-of-input after this

        # Repeat files num_epoch times
        dataset = dataset.repeat(count = num_epochs)

        # Group the data into batches
        dataset = dataset.batch(batch_size = batch_size)
        
        # Determine if we should shuffle based on if we are training or evaluating
        if mode == tf.estimator.ModeKeys.TRAIN:
            dataset = dataset.shuffle(buffer_size = 10 * batch_size)

        # Create a iterator and then pull the next batch of features from the example queue
        batched_dataset = dataset.make_one_shot_iterator().get_next()

        return batched_dataset
    return _input_fn

# Create our model function to be used in our custom estimator
def lstm_encoder_decoder_autoencoder_anomaly_detection(features, labels, mode, params):
    print("\nlstm_encoder_decoder_autoencoder_anomaly_detection: features = \n{}".format(features))
    print("lstm_encoder_decoder_autoencoder_anomaly_detection: labels = \n{}".format(labels))
    print("lstm_encoder_decoder_autoencoder_anomaly_detection: mode = \n{}".format(mode))
    print("lstm_encoder_decoder_autoencoder_anomaly_detection: params = \n{}".format(params))

    # 0. Get input sequence tensor into correct shape
    # Get dynamic batch size in case there was a partially filled batch
    current_batch_size = tf.shape(input = features[UNLABELED_CSV_COLUMNS[0]], out_type = tf.int64)[0]

    # Get the number of features 
    number_of_features = len(UNLABELED_CSV_COLUMNS)

    # Stack all of the features into a 3-D tensor
    X = tf.stack(values = list(features.values()), axis = 2) # shape = (current_batch_size, sequence_length, number_of_features)

    # Unstack all of 3-D features tensor into a sequence(list) of 2-D tensors of shape = (current_batch_size, number_of_features)
    X_sequence = tf.unstack(value = X, num = params["sequence_length"], axis = 1)

    # Since this is an autoencoder, the features are the labels. It works better though to have the labels in reverse order
    if params["reverse_labels_sequence"] == True:
        Y = tf.reverse_sequence(input = X,  # shape = (current_batch_size, sequence_length, number_of_features)
                                seq_lengths = tf.tile(input = tf.constant(value = [params["sequence_length"]], dtype = tf.int64), 
                                                      multiples = tf.expand_dims(input = current_batch_size, axis = 0)), 
                                seq_axis = 1, 
                                batch_axis = 0)
    else:
        Y = X  # shape = (current_batch_size, sequence_length, number_of_features)
  
  ################################################################################
  
    # 1. Create encoder of encoder-decoder LSTM stacks
    def create_LSTM_stack(lstm_hidden_units, lstm_dropout_output_keep_probs):
        # First create a list of LSTM cells using our list of lstm hidden unit sizes
        lstm_cells = [tf.contrib.rnn.BasicLSTMCell(num_units = units, forget_bias = 1.0, state_is_tuple = True) for units in lstm_hidden_units] # list of LSTM cells

        # Next apply a dropout wrapper to our stack of LSTM cells, in this case just on the outputs
        dropout_lstm_cells = [tf.nn.rnn_cell.DropoutWrapper(cell = lstm_cells[cell_index], 
                                                            input_keep_prob = 1.0, 
                                                            output_keep_prob = lstm_dropout_output_keep_probs[cell_index], 
                                                            state_keep_prob = 1.0) for cell_index in range(len(lstm_cells))]

        # Create a stack of layers of LSTM cells
        stacked_lstm_cells = tf.contrib.rnn.MultiRNNCell(cells = dropout_lstm_cells, state_is_tuple = True) # combines list into MultiRNNCell object

        return stacked_lstm_cells
  
    # Create our decoder now
    decoder_stacked_lstm_cells = create_LSTM_stack(params["decoder_lstm_hidden_units"], params["lstm_dropout_output_keep_probs"])
  
    # Create the encoder variable scope
    with tf.variable_scope("encoder"):
        # Create separate encoder cells with their own weights separate from decoder
        encoder_stacked_lstm_cells = create_LSTM_stack(params["encoder_lstm_hidden_units"], params["lstm_dropout_output_keep_probs"])

        # Encode the input sequence using our encoder stack of LSTMs
        # encoder_outputs = list sequence_length long of shape = (current_batch_size, encoder_lstm_hidden_units[-1]), # encoder_states = tuple of final encoder c_state and h_state for each layer
        encoder_outputs, encoder_states = tf.nn.static_rnn(cell = encoder_stacked_lstm_cells, 
                                                           inputs = X_sequence, 
                                                           initial_state = encoder_stacked_lstm_cells.zero_state(batch_size = tf.cast(x = current_batch_size, dtype = tf.int32), dtype = tf.float64), 
                                                           dtype = tf.float64)

        # We just pass on the final c and h states of the encoder"s last layer, so extract that and drop the others
        encoder_final_states = encoder_states[-1] # LSTMStateTuple shape = (current_batch_size, lstm_hidden_units[-1])

        # Extract the c and h states from the tuple
        encoder_final_c, encoder_final_h = encoder_final_states # both have shape = (current_batch_size, lstm_hidden_units[-1])

        # In case the decoder"s first layer"s number of units is different than encoder's last layer's number of units, use a dense layer to map to the correct shape
        encoder_final_c_dense = tf.layers.dense(inputs = encoder_final_c, units = params["decoder_lstm_hidden_units"][0], activation = None) # shape = (current_batch_size, decoder_lstm_hidden_units[0])
        encoder_final_h_dense = tf.layers.dense(inputs = encoder_final_h, units = params["decoder_lstm_hidden_units"][0], activation = None) # shape = (current_batch_size, decoder_lstm_hidden_units[0])

        # The decoder"s first layer"s state comes from the encoder, the rest of the layers" initial states are zero
        decoder_intial_states = tuple([tf.contrib.rnn.LSTMStateTuple(c = encoder_final_c_dense, h = encoder_final_h_dense)] + \
                                      [tf.contrib.rnn.LSTMStateTuple(c = tf.zeros(shape = [current_batch_size, units], dtype = tf.float64), 
                                                                     h = tf.zeros(shape = [current_batch_size, units], dtype = tf.float64)) for units in params["decoder_lstm_hidden_units"][1:]])
    
    ################################################################################

    # 2. Create decoder of encoder-decoder LSTM stacks
    # The rnn_decoder function takes labels during TRAIN/EVAL and a start token followed by its previous predictions during PREDICT
    # Starts with an intial state of the final encoder states
    def rnn_decoder(decoder_inputs, initial_state, cell, inference):
        # Create the decoder variable scope
        with tf.variable_scope("decoder"):
            # Load in our initial state from our encoder
            state = initial_state # tuple of final encoder c_state and h_state of final encoder layer
            
            # Create an empty list to store our hidden state output for every timestep
            outputs = []
            
            # Begin with no previous output
            previous_output = None
            
            # Loop over all of our decoder_inputs which will be sequence_length long
            for index, decoder_input in enumerate(decoder_inputs):
                # If there has been a previous output then we will determine the next input
                if previous_output is not None:
                    # Create the input layer to our DNN
                    network = previous_output # shape = (current_batch_size, lstm_hidden_units[-1])
                    
                    # Create our dnn variable scope
                    with tf.variable_scope(name_or_scope = "dnn", reuse = tf.AUTO_REUSE):
                        # Add hidden layers with the given number of units/neurons per layer
                        for units in params["dnn_hidden_units"]:
                            network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size, dnn_hidden_units[i])
                            
                        # Connect the final hidden layer to a dense layer with no activation to get the logits
                        logits = tf.layers.dense(inputs = network, units = number_of_features, activation = None) # shape = (current_batch_size, number_of_features)
                    
                    # If we are in inference then we will overwrite our next decoder_input with the logits we just calculated.
                    # Otherwise, we leave the decoder_input input as it was from the enumerated list
                    # We have to calculate the logits even when not using them so that the correct dnn subgraph will be generated here and after the encoder-decoder for both training and inference
                    if inference == True:
                        decoder_input = logits # shape = (current_batch_size, number_of_features)

                # If this isn"t our first time through the loop, just reuse(share) the same variables for each iteration within the current variable scope
                if index > 0:
                    tf.get_variable_scope().reuse_variables()
                
                # Run the decoder input through the decoder stack picking up from the previous state
                output, state = cell(decoder_input, state) # output = shape = (current_batch_size, lstm_hidden_units[-1]), state = # tuple of final decoder c_state and h_state
                
                # Append the current decoder hidden state output to the outputs list
                outputs.append(output) # growing list eventually sequence_length long of shape = (current_batch_size, lstm_hidden_units[-1])
                
                # Set the previous output to the output just calculated
                previous_output = output # shape = (current_batch_size, lstm_hidden_units[-1])
        return outputs, state
  
    # Train our decoder now
  
    # Encoder-decoders work differently during training/evaluation and inference so we will have two separate subgraphs for each
    if mode == tf.estimator.ModeKeys.TRAIN and params["evaluation_mode"] == "reconstruction":
        # Break 3-D labels tensor into a list of 2-D tensors
        unstacked_labels = tf.unstack(value = Y, num = params["sequence_length"], axis = 1) # list of sequence_length long of shape = (current_batch_size, number_of_features)

        # Call our decoder using the labels as our inputs, the encoder final state as our initial state, our other LSTM stack as our cells, and inference set to false
        decoder_outputs, decoder_states = rnn_decoder(decoder_inputs = unstacked_labels, initial_state = decoder_intial_states, cell = decoder_stacked_lstm_cells, inference = False)
    else:
        # Since this is inference create fake labels. The list length needs to be the output sequence length even though only the first element is the only one actually used (as our go signal)
        fake_labels = [tf.zeros(shape = [current_batch_size, number_of_features], dtype = tf.float64) for _ in range(params["sequence_length"])]
        
        # Call our decoder using fake labels as our inputs, the encoder final state as our initial state, our other LSTM stack as our cells, and inference set to true
        # decoder_outputs = list sequence_length long of shape = (current_batch_size, decoder_lstm_hidden_units[-1]), # decoder_states = tuple of final decoder c_state and h_state for each layer
        decoder_outputs, decoder_states = rnn_decoder(decoder_inputs = fake_labels, initial_state = decoder_intial_states, cell = decoder_stacked_lstm_cells, inference = True)
    
    # Stack together the list of rank 2 decoder output tensors into one rank 3 tensor
    stacked_decoder_outputs = tf.stack(values = decoder_outputs, axis = 1) # shape = (current_batch_size, sequence_length, lstm_hidden_units[-1])
    
    # Reshape rank 3 decoder outputs into rank 2 by folding sequence length into batch size
    reshaped_stacked_decoder_outputs = tf.reshape(tensor = stacked_decoder_outputs, shape = [current_batch_size * params["sequence_length"], params["decoder_lstm_hidden_units"][-1]]) # shape = (current_batch_size * sequence_length, lstm_hidden_units[-1])

    ################################################################################
    
    # 3. Create the DNN structure now after the encoder-decoder LSTM stack
    # Create the input layer to our DNN
    network = reshaped_stacked_decoder_outputs # shape = (current_batch_size * sequence_length, lstm_hidden_units[-1])
    
    # Reuse the same variable scope as we used within our decoder (for inference)
    with tf.variable_scope(name_or_scope = "dnn", reuse = tf.AUTO_REUSE):
        # Add hidden layers with the given number of units/neurons per layer
        for units in params["dnn_hidden_units"]:
            network = tf.layers.dense(inputs = network, units = units, activation = tf.nn.relu) # shape = (current_batch_size * sequence_length, dnn_hidden_units[i])

        # Connect the final hidden layer to a dense layer with no activation to get the logits
        logits = tf.layers.dense(inputs = network, units = number_of_features, activation = None) # shape = (current_batch_size * sequence_length, number_of_features)
    
    # Now that we are through the final DNN for each sequence element for each example in the batch, reshape the predictions to match our labels
    predictions = tf.reshape(tensor = logits, shape = [current_batch_size, params["sequence_length"], number_of_features]) # shape = (current_batch_size, sequence_length, number_of_features)
    
    # Variables for calculating error distribution statistics
    with tf.variable_scope(name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
        # Time based
        absolute_error_count_batch_time_variable = tf.get_variable(name = "absolute_error_count_batch_time_variable", # shape = ()
                                                                   dtype = tf.int64,
                                                                   initializer = tf.zeros(shape = [], 
                                                                                          dtype = tf.int64),
                                                                   trainable = False)
        
        absolute_error_mean_batch_time_variable = tf.get_variable(name = "absolute_error_mean_batch_time_variable", # shape = (number_of_features,)
                                                                  dtype = tf.float64,
                                                                  initializer = tf.zeros(shape = [number_of_features], 
                                                                                         dtype = tf.float64),
                                                                  trainable = False)
        
        absolute_error_covariance_matrix_batch_time_variable = tf.get_variable(name = "absolute_error_covariance_matrix_batch_time_variable", # shape = (number_of_features, number_of_features)
                                                                               dtype = tf.float64,
                                                                               initializer = tf.zeros(shape = [number_of_features, number_of_features], 
                                                                                                      dtype = tf.float64),
                                                                               trainable = False)

        absolute_error_inverse_covariance_matrix_batch_time_variable = tf.get_variable(name = "absolute_error_inverse_covariance_matrix_batch_time_variable", # shape = (number_of_features, number_of_features)
                                                                                       dtype = tf.float64,
                                                                                       initializer = tf.zeros(shape = [number_of_features, number_of_features], 
                                                                                                              dtype = tf.float64),
                                                                                       trainable = False)

        # Features based
        absolute_error_count_batch_features_variable = tf.get_variable(name = "absolute_error_count_batch_features_variable", # shape = ()
                                                                       dtype = tf.int64,
                                                                       initializer = tf.zeros(shape = [], 
                                                                                              dtype = tf.int64),
                                                                       trainable = False)
        
        absolute_error_mean_batch_features_variable = tf.get_variable(name = "absolute_error_mean_batch_features_variable", # shape = (sequence_length,)
                                                                      dtype = tf.float64,
                                                                      initializer = tf.zeros(shape = [params["sequence_length"]], 
                                                                                             dtype = tf.float64),
                                                                      trainable = False)
        
        absolute_error_covariance_matrix_batch_features_variable = tf.get_variable(name = "absolute_error_covariance_matrix_batch_features_variable", # shape = (sequence_length, sequence_length)
                                                                                   dtype = tf.float64,
                                                                                   initializer = tf.zeros(shape = [params["sequence_length"], params["sequence_length"]], 
                                                                                                          dtype = tf.float64),
                                                                                   trainable = False)

        absolute_error_inverse_covariance_matrix_batch_features_variable = tf.get_variable(name = "absolute_error_inverse_covariance_matrix_batch_features_variable", # shape = (sequence_length, sequence_length)
                                                                                           dtype = tf.float64,
                                                                                           initializer = tf.zeros(shape = [params["sequence_length"], params["sequence_length"]], 
                                                                                                                  dtype = tf.float64),
                                                                                           trainable = False)
    
    # Variables for automatically tuning anomaly thresholds
    with tf.variable_scope(name_or_scope = "mahalanobis_distance_threshold_variables", reuse = tf.AUTO_REUSE):
        # Time based
        true_positives_at_thresholds_time_variable = tf.get_variable(name = "true_positives_at_thresholds_time_variable", # shape = (number_of_batch_time_anomaly_thresholds,)
                                                                     dtype = tf.int64,
                                                                     initializer = tf.zeros(shape = [params["number_of_batch_time_anomaly_thresholds"]], 
                                                                                            dtype = tf.int64),
                                                                     trainable = False)

        false_negatives_at_thresholds_time_variable = tf.get_variable(name = "false_negatives_at_thresholds_time_variable", # shape = (number_of_batch_time_anomaly_thresholds,)
                                                                      dtype = tf.int64,
                                                                      initializer = tf.zeros(shape = [params["number_of_batch_time_anomaly_thresholds"]], 
                                                                                             dtype = tf.int64),
                                                                      trainable = False)

        false_positives_at_thresholds_time_variable = tf.get_variable(name = "false_positives_at_thresholds_time_variable", # shape = (number_of_batch_time_anomaly_thresholds,)
                                                                      dtype = tf.int64,
                                                                      initializer = tf.zeros(shape = [params["number_of_batch_time_anomaly_thresholds"]], 
                                                                                             dtype = tf.int64),
                                                                      trainable = False)

        true_negatives_at_thresholds_time_variable = tf.get_variable(name = "true_negatives_at_thresholds_time_variable", # shape = (number_of_batch_time_anomaly_thresholds,)
                                                                     dtype = tf.int64,
                                                                     initializer = tf.zeros(shape = [params["number_of_batch_time_anomaly_thresholds"]], 
                                                                                            dtype = tf.int64),
                                                                     trainable = False)
        
        time_anomaly_threshold_variable = tf.get_variable(name = "time_anomaly_threshold_variable", # shape = ()
                                                          dtype = tf.float64,
                                                          initializer = tf.zeros(shape = [], 
                                                                                 dtype = tf.float64),
                                                          trainable = False)

        # Features based
        true_positives_at_thresholds_features_variable = tf.get_variable(name = "true_positives_at_thresholds_features_variable", # shape = (number_of_batch_features_anomaly_thresholds,)
                                                                         dtype = tf.int64,
                                                                         initializer = tf.zeros(shape = [params["number_of_batch_features_anomaly_thresholds"]], 
                                                                                                dtype = tf.int64),
                                                                         trainable = False)

        false_negatives_at_thresholds_features_variable = tf.get_variable(name = "false_negatives_at_thresholds_features_variable", # shape = (number_of_batch_features_anomaly_thresholds,)
                                                                          dtype = tf.int64,
                                                                          initializer = tf.zeros(shape = [params["number_of_batch_features_anomaly_thresholds"]], 
                                                                                                 dtype = tf.int64),
                                                                          trainable = False)

        false_positives_at_thresholds_features_variable = tf.get_variable(name = "false_positives_at_thresholds_features_variable", # shape = (number_of_batch_features_anomaly_thresholds,)
                                                                          dtype = tf.int64,
                                                                          initializer = tf.zeros(shape = [params["number_of_batch_features_anomaly_thresholds"]], 
                                                                                                 dtype = tf.int64),
                                                                          trainable = False)

        true_negatives_at_thresholds_features_variable = tf.get_variable(name = "true_negatives_at_thresholds_features_variable", # shape = (number_of_batch_features_anomaly_thresholds,)
                                                                         dtype = tf.int64,
                                                                         initializer = tf.zeros(shape = [params["number_of_batch_features_anomaly_thresholds"]], 
                                                                                                dtype = tf.int64),
                                                                         trainable = False)
        
        features_anomaly_threshold_variable = tf.get_variable(name = "features_anomaly_threshold_variable", # shape = ()
                                                              dtype = tf.float64,
                                                              initializer = tf.zeros(shape = [], 
                                                                                     dtype = tf.float64),
                                                              trainable = False)
        
    # Variables for automatically tuning anomaly thresholds
    with tf.variable_scope(name_or_scope = "anomaly_threshold_eval_variables", reuse = tf.AUTO_REUSE):
        # Time based
        true_positives_at_threshold_eval_time_variable = tf.get_variable(name = "true_positives_at_threshold_eval_time_variable", # shape = ()
                                                                         dtype = tf.int64,
                                                                         initializer = tf.zeros(shape = [], 
                                                                                                dtype = tf.int64),
                                                                         trainable = False)

        false_negatives_at_threshold_eval_time_variable = tf.get_variable(name = "false_negatives_at_threshold_eval_time_variable", # shape = ()
                                                                          dtype = tf.int64,
                                                                          initializer = tf.zeros(shape = [], 
                                                                                                 dtype = tf.int64),
                                                                          trainable = False)

        false_positives_at_threshold_eval_time_variable = tf.get_variable(name = "false_positives_at_threshold_eval_time_variable", # shape = ()
                                                                          dtype = tf.int64,
                                                                          initializer = tf.zeros(shape = [], 
                                                                                                 dtype = tf.int64),
                                                                          trainable = False)

        true_negatives_at_threshold_eval_time_variable = tf.get_variable(name = "true_negatives_at_threshold_eval_time_variable", # shape = ()
                                                                         dtype = tf.int64,
                                                                         initializer = tf.zeros(shape = [], 
                                                                                                dtype = tf.int64),
                                                                         trainable = False)
        
        accuracy_at_threshold_eval_time_variable = tf.get_variable(name = "accuracy_at_threshold_eval_time_variable", # shape = ()
                                                                   dtype = tf.float64,
                                                                   initializer = tf.zeros(shape = [], 
                                                                                          dtype = tf.float64),
                                                                   trainable = False)
        
        precision_at_threshold_eval_time_variable = tf.get_variable(name = "precision_at_threshold_eval_time_variable", # shape = ()
                                                                    dtype = tf.float64,
                                                                    initializer = tf.zeros(shape = [], 
                                                                                           dtype = tf.float64),
                                                                    trainable = False)
        
        recall_at_threshold_eval_time_variable = tf.get_variable(name = "recall_at_threshold_eval_time_variable", # shape = ()
                                                                 dtype = tf.float64,
                                                                 initializer = tf.zeros(shape = [], 
                                                                                        dtype = tf.float64),
                                                                 trainable = False)
        
        f_beta_score_at_threshold_eval_time_variable = tf.get_variable(name = "f_beta_score_at_threshold_eval_time_variable", # shape = ()
                                                                       dtype = tf.float64,
                                                                       initializer = tf.zeros(shape = [], 
                                                                                              dtype = tf.float64),
                                                                       trainable = False)

        # Features based
        true_positives_at_threshold_eval_features_variable = tf.get_variable(name = "true_positives_at_threshold_eval_features_variable", # shape = ()
                                                                             dtype = tf.int64,
                                                                             initializer = tf.zeros(shape = [], 
                                                                                                    dtype = tf.int64),
                                                                             trainable = False)

        false_negatives_at_threshold_eval_features_variable = tf.get_variable(name = "false_negatives_at_threshold_eval_features_variable", # shape = ()
                                                                              dtype = tf.int64,
                                                                              initializer = tf.zeros(shape = [], 
                                                                                                     dtype = tf.int64),
                                                                              trainable = False)

        false_positives_at_threshold_eval_features_variable = tf.get_variable(name = "false_positives_at_threshold_eval_features_variable", # shape = ()
                                                                              dtype = tf.int64,
                                                                              initializer = tf.zeros(shape = [], 
                                                                                                     dtype = tf.int64),
                                                                              trainable = False)

        true_negatives_at_threshold_eval_features_variable = tf.get_variable(name = "true_negatives_at_threshold_eval_features_variable", # shape = ()
                                                                             dtype = tf.int64,
                                                                             initializer = tf.zeros(shape = [], 
                                                                                                    dtype = tf.int64),
                                                                             trainable = False)
        
        accuracy_at_threshold_eval_features_variable = tf.get_variable(name = "accuracy_at_threshold_eval_features_variable", # shape = ()
                                                                   dtype = tf.float64,
                                                                   initializer = tf.zeros(shape = [], 
                                                                                          dtype = tf.float64),
                                                                   trainable = False)
        
        precision_at_threshold_eval_features_variable = tf.get_variable(name = "precision_at_threshold_eval_features_variable", # shape = ()
                                                                    dtype = tf.float64,
                                                                    initializer = tf.zeros(shape = [], 
                                                                                           dtype = tf.float64),
                                                                    trainable = False)
        
        recall_at_threshold_eval_features_variable = tf.get_variable(name = "recall_at_threshold_eval_features_variable", # shape = ()
                                                                 dtype = tf.float64,
                                                                 initializer = tf.zeros(shape = [], 
                                                                                        dtype = tf.float64),
                                                                 trainable = False)
        
        f_beta_score_at_threshold_eval_features_variable = tf.get_variable(name = "f_beta_score_at_threshold_eval_features_variable", # shape = ()
                                                                       dtype = tf.float64,
                                                                       initializer = tf.zeros(shape = [], 
                                                                                              dtype = tf.float64),
                                                                       trainable = False)

    dummy_variable = tf.get_variable(name = "dummy_variable", # shape = ()
                                     dtype = tf.float64,
                                     initializer = tf.zeros(shape = [], dtype = tf.float64),
                                     trainable = True)
    
    # Now branch off based on which mode we are in
    predictions_dict = None
    loss = None
    train_op = None
    eval_metric_ops = None
    export_outputs = None
    
    # 3. Loss function, training/eval ops
    if mode == tf.estimator.ModeKeys.TRAIN and params["evaluation_mode"] != "tune_anomaly_thresholds":
        if params["evaluation_mode"] == "reconstruction":
            loss = tf.losses.mean_squared_error(labels = Y, predictions = predictions)

            train_op = tf.contrib.layers.optimize_loss(
                loss = loss,
                global_step = tf.train.get_global_step(),
                learning_rate = params["learning_rate"],
                optimizer = "Adam")
        elif params["evaluation_mode"] == "calculate_error_distribution_statistics":
            error = Y - predictions # shape = (current_batch_size, sequence_length, number_of_features)
            
            absolute_error = tf.abs(x = error) # shape = (current_batch_size, sequence_length, number_of_features)

            ################################################################################

            with tf.variable_scope(name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
                # This function updates the count of records used
                def update_count(count_a, count_b):
                    return count_a + count_b
                
                # This function updates the mahalanobis distance variables when the number_of_rows equals 1
                def singleton_batch_mahalanobis_distance_variable_updating(inner_size, absolute_error_reshaped, absolute_error_count_variable, absolute_error_mean_variable, absolute_error_covariance_matrix_variable, absolute_error_inverse_covariance_matrix_variable):
                    # This function updates the mean vector incrementally
                    def update_mean_incremental(count_a, mean_a, value_b):
                        return (mean_a * tf.cast(x = count_a, dtype = tf.float64) + tf.squeeze(input = value_b, axis = 0)) / tf.cast(x = count_a + 1, dtype = tf.float64)

                    # This function updates the covariance matrix incrementally
                    def update_covariance_incremental(count_a, mean_a, cov_a, value_b, mean_ab, sample_covariance):
                        if sample_covariance == True:
                            cov_ab = (cov_a * tf.cast(x = count_a - 1, dtype = tf.float64) + tf.matmul(a = value_b - mean_a, b = value_b - mean_ab, transpose_a = True)) / tf.cast(x = count_a, dtype = tf.float64)
                        else:
                            cov_ab = (cov_a * tf.cast(x = count_a, dtype = tf.float64) + tf.matmul(a = value_b - mean_a, b = value_b - mean_ab, transpose_a = True)) / tf.cast(x = count_a + 1, dtype = tf.float64)
                        return cov_ab

                    # Calculate new combined mean to use for incremental covariance matrix calculation
                    mean_ab = update_mean_incremental(count_a = absolute_error_count_variable, 
                                                      mean_a = absolute_error_mean_variable, 
                                                      value_b = absolute_error_reshaped) # time_shape = (number_of_features,), features_shape = (sequence_length,)

                    # Update running variables from single example
                    absolute_error_count_tensor = update_count(count_a = absolute_error_count_variable, 
                                                               count_b = 1) # time_shape = (), features_shape = ()
                    
                    absolute_error_mean_tensor = mean_ab # time_shape = (number_of_features,), features_shape = (sequence_length,)

                    if inner_size == 1:
                        absolute_error_covariance_matrix_tensor = tf.zeros_like(tensor = absolute_error_covariance_matrix_variable, dtype = tf.float64)
                        absolute_error_inverse_covariance_matrix_tensor = tf.eye(num_rows = tf.shape(input = absolute_error_covariance_matrix_tensor)[0], 
                                                                                                     dtype = tf.float64) / params["eps"]
                    else:
                        absolute_error_covariance_matrix_tensor = update_covariance_incremental(count_a = absolute_error_count_variable, 
                                                                                                mean_a = absolute_error_mean_variable, 
                                                                                                cov_a = absolute_error_covariance_matrix_variable, 
                                                                                                value_b = absolute_error_reshaped, 
                                                                                                mean_ab = mean_ab, 
                                                                                                sample_covariance = True) # time_shape = (number_of_features, number_of_features), features_shape = (sequence_length, sequence_length)
                    
                        absolute_error_inverse_covariance_matrix_tensor = tf.matrix_inverse(input = absolute_error_covariance_matrix_tensor + \
                                                                                            tf.eye(num_rows = tf.shape(input = absolute_error_covariance_matrix_tensor)[0], 
                                                                                                   dtype = tf.float64) * params["eps"]) # time_shape = (number_of_features, number_of_features), features_shape = (sequence_length, sequence_length)

                    # Assign values to variables, use control dependencies around return to enforce the mahalanobis variables to be assigned, the control order matters, hence the separate contexts
                    with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_covariance_matrix_variable, value = absolute_error_covariance_matrix_tensor)]):
                        with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_mean_variable, value = absolute_error_mean_tensor)]):
                            with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_count_variable, value = absolute_error_count_tensor)]):
                                with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_inverse_covariance_matrix_variable, value = absolute_error_inverse_covariance_matrix_tensor)]):
                                    return tf.identity(input = absolute_error_covariance_matrix_variable), tf.identity(input = absolute_error_mean_variable), tf.identity(input = absolute_error_count_variable), tf.identity(input = absolute_error_inverse_covariance_matrix_variable)
                
                # This function updates the mahalanobis distance variables when the number_of_rows does NOT equal 1
                def non_singleton_batch_mahalanobis_distance_variable_updating(current_batch_size, inner_size, absolute_error_reshaped, absolute_error_count_variable, absolute_error_mean_variable, absolute_error_covariance_matrix_variable, absolute_error_inverse_covariance_matrix_variable):
                    # This function updates the mean vector using a batch of data
                    def update_mean_batch(count_a, mean_a, count_b, mean_b):
                        return (mean_a * tf.cast(x = count_a, dtype = tf.float64) + mean_b * tf.cast(x = count_b, dtype = tf.float64)) / tf.cast(x = count_a + count_b, dtype = tf.float64)

                    # This function updates the covariance matrix using a batch of data
                    def update_covariance_batch(count_a, mean_a, cov_a, count_b, mean_b, cov_b, sample_covariance):
                        mean_diff = tf.expand_dims(input = mean_a - mean_b, axis = 0)

                        if sample_covariance == True:
                            cov_ab = (cov_a * tf.cast(x = count_a - 1, dtype = tf.float64) + cov_b * tf.cast(x = count_b - 1, dtype = tf.float64) + tf.matmul(a = mean_diff, b = mean_diff, transpose_a = True) * tf.cast(x = count_a * count_b, dtype = tf.float64) / tf.cast(x = count_a + count_b, dtype = tf.float64)) / tf.cast(x = count_a + count_b - 1, dtype = tf.float64)
                        else:
                            cov_ab = (cov_a * tf.cast(x = count_a, dtype = tf.float64) + cov_b * tf.cast(x = count_b, dtype = tf.float64) + tf.matmul(a = mean_diff, b = mean_diff, transpose_a = True) * tf.cast(x = count_a * count_b, dtype = tf.float64) / tf.cast(x = count_a + count_b, dtype = tf.float64)) / tf.cast(x = count_a + count_b, dtype = tf.float64)
                        return cov_ab                    
                    
                    # Find statistics of batch
                    number_of_rows = current_batch_size * inner_size
                    
                    absolute_error_reshaped_mean = tf.reduce_mean(input_tensor = absolute_error_reshaped, axis = 0) # time_shape = (number_of_features,), features_shape = (sequence_length,)

                    absolute_error_reshaped_centered = absolute_error_reshaped - absolute_error_reshaped_mean # time_shape = (current_batch_size * sequence_length, number_of_features), features_shape = (current_batch_size * number_of_features, sequence_length)

                    if inner_size > 1:
                        absolute_error_reshaped_covariance_matrix = tf.matmul(a = absolute_error_reshaped_centered, # time_shape = (number_of_features, number_of_features), features_shape = (sequence_length, sequence_length)
                                                                              b = absolute_error_reshaped_centered, 
                                                                              transpose_a = True) / tf.cast(x = number_of_rows - 1, dtype = tf.float64)

                    # Update running variables from batch statistics
                    absolute_error_count_tensor = update_count(count_a = absolute_error_count_variable, 
                                                               count_b = number_of_rows) # time_shape = (), features_shape = ()
                    
                    absolute_error_mean_tensor = update_mean_batch(count_a = absolute_error_count_variable, 
                                                                   mean_a = absolute_error_mean_variable, 
                                                                   count_b = number_of_rows, 
                                                                   mean_b = absolute_error_reshaped_mean) # time_shape = (number_of_features,), features_shape = (sequence_length,)

                    if inner_size == 1:
                        absolute_error_covariance_matrix_tensor = tf.zeros_like(tensor = absolute_error_covariance_matrix_variable, dtype = tf.float64)
                        absolute_error_inverse_covariance_matrix_tensor = tf.eye(num_rows = tf.shape(input = absolute_error_covariance_matrix_tensor)[0], 
                                                                                                     dtype = tf.float64) / params["eps"]
                    else:
                        absolute_error_covariance_matrix_tensor = update_covariance_batch(count_a = absolute_error_count_variable, 
                                                                                          mean_a = absolute_error_mean_variable, 
                                                                                          cov_a = absolute_error_covariance_matrix_variable, 
                                                                                          count_b = number_of_rows, 
                                                                                          mean_b = absolute_error_reshaped_mean, 
                                                                                          cov_b = absolute_error_reshaped_covariance_matrix, 
                                                                                          sample_covariance = True) # time_shape = (number_of_features, number_of_features), features_shape = (sequence_length, sequence_length)

                        absolute_error_inverse_covariance_matrix_tensor = tf.matrix_inverse(input = absolute_error_covariance_matrix_tensor + \
                                                                                            tf.eye(num_rows = tf.shape(input = absolute_error_covariance_matrix_tensor)[0], 
                                                                                                   dtype = tf.float64) * params["eps"]) # time_shape = (number_of_features, number_of_features), features_shape = (sequence_length, sequence_length)
                    
                    # Assign values to variables, use control dependencies around return to enforce the mahalanobis variables to be assigned, the control order matters, hence the separate contexts
                    with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_covariance_matrix_variable, value = absolute_error_covariance_matrix_tensor)]):
                        with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_mean_variable, value = absolute_error_mean_tensor)]):
                            with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_count_variable, value = absolute_error_count_tensor)]):
                                with tf.control_dependencies(control_inputs = [tf.assign(ref = absolute_error_inverse_covariance_matrix_variable, value = absolute_error_inverse_covariance_matrix_tensor)]):
                                    return tf.identity(input = absolute_error_covariance_matrix_variable), tf.identity(input = absolute_error_mean_variable), tf.identity(input = absolute_error_count_variable), tf.identity(input = absolute_error_inverse_covariance_matrix_variable)
                
                # Check if batch is a singleton or not, very important for covariance math
                
                # Time based ########################################
                absolute_error_reshaped_batch_time = tf.reshape(tensor = absolute_error, 
                                                                shape = [current_batch_size * params["sequence_length"], number_of_features]) # shape = (current_batch_size * sequence_length, number_of_features)
                
                singleton_batch_time_condition = tf.equal(x = current_batch_size * params["sequence_length"], y = 1) # shape = ()
                
                covariance_batch_time_variable, mean_batch_time_variable, count_batch_time_variable, inverse_batch_time_variable = \
                    tf.cond(pred = singleton_batch_time_condition, 
                            true_fn = lambda: singleton_batch_mahalanobis_distance_variable_updating(params["sequence_length"], absolute_error_reshaped_batch_time, absolute_error_count_batch_time_variable, absolute_error_mean_batch_time_variable, absolute_error_covariance_matrix_batch_time_variable, absolute_error_inverse_covariance_matrix_batch_time_variable), 
                            false_fn = lambda: non_singleton_batch_mahalanobis_distance_variable_updating(current_batch_size, params["sequence_length"], absolute_error_reshaped_batch_time, absolute_error_count_batch_time_variable, absolute_error_mean_batch_time_variable, absolute_error_covariance_matrix_batch_time_variable, absolute_error_inverse_covariance_matrix_batch_time_variable))

                # Features based ########################################
                absolute_error_transposed_batch_features = tf.transpose(a = absolute_error, perm = [0, 2, 1]) # shape = (current_batch_size, number_of_features, sequence_length)

                absolute_error_reshaped_batch_features = tf.reshape(tensor = absolute_error_transposed_batch_features, 
                                                                    shape = [current_batch_size * number_of_features, params["sequence_length"]]) # shape = (current_batch_size * number_of_features, sequence_length)

                singleton_batch_features_condition = tf.equal(x = current_batch_size * number_of_features, y = 1) # shape = ()
                
                covariance_batch_features_variable, mean_batch_features_variable, count_batch_features_variable, inverse_batch_features_variable = \
                    tf.cond(pred = singleton_batch_features_condition, 
                            true_fn = lambda: singleton_batch_mahalanobis_distance_variable_updating(number_of_features, absolute_error_reshaped_batch_features, absolute_error_count_batch_features_variable, absolute_error_mean_batch_features_variable, absolute_error_covariance_matrix_batch_features_variable, absolute_error_inverse_covariance_matrix_batch_features_variable), 
                            false_fn = lambda: non_singleton_batch_mahalanobis_distance_variable_updating(current_batch_size, number_of_features, absolute_error_reshaped_batch_features, absolute_error_count_batch_features_variable, absolute_error_mean_batch_features_variable, absolute_error_covariance_matrix_batch_features_variable, absolute_error_inverse_covariance_matrix_batch_features_variable))

            # Lastly use control dependencies around loss to enforce the mahalanobis variables to be assigned, the control order matters, hence the separate contexts
            with tf.control_dependencies(control_inputs = [covariance_batch_time_variable, covariance_batch_features_variable]):
                with tf.control_dependencies(control_inputs = [mean_batch_time_variable, mean_batch_features_variable]):
                    with tf.control_dependencies(control_inputs = [count_batch_time_variable, count_batch_features_variable]):
                        with tf.control_dependencies(control_inputs = [inverse_batch_time_variable, inverse_batch_features_variable]):
                            loss = tf.reduce_sum(input_tensor = tf.zeros(shape = (), dtype = tf.float64) * dummy_variable)

                            train_op = tf.contrib.layers.optimize_loss(
                                loss = loss,
                                global_step = tf.train.get_global_step(),
                                learning_rate = params["learning_rate"],
                                optimizer = "SGD")
    elif mode == tf.estimator.ModeKeys.EVAL and params["evaluation_mode"] != "tune_anomaly_thresholds":
        # Reconstruction loss on evaluation set
        loss = tf.losses.mean_squared_error(labels = Y, predictions = predictions)
        
        if params["evaluation_mode"] == "reconstruction": # if reconstruction during train_and_evaluate
            # Reconstruction eval metrics
            eval_metric_ops = {
                "rmse": tf.metrics.root_mean_squared_error(labels = Y, predictions = predictions),
                "mae": tf.metrics.mean_absolute_error(labels = Y, predictions = predictions)
            }
    elif mode == tf.estimator.ModeKeys.PREDICT or ((mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL) and params["evaluation_mode"] == "tune_anomaly_thresholds"):
        def mahalanobis_distance(error_vectors_reshaped, mean_vector, inverse_covariance_matrix, final_shape):
            error_vectors_reshaped_centered = error_vectors_reshaped - mean_vector # time_shape = (current_batch_size * sequence_length, number_of_features), features_shape = (current_batch_size * number_of_features, sequence_length)

            mahalanobis_right_matrix_product = tf.matmul(a = inverse_covariance_matrix, # time_shape = (number_of_features, current_batch_size * sequence_length), features_shape = (sequence_length, current_batch_size * number_of_features)
                                                         b = error_vectors_reshaped_centered,
                                                         transpose_b = True)


            mahalanobis_distance_vectorized = tf.matmul(a = error_vectors_reshaped_centered, # time_shape = (current_batch_size * sequence_length, current_batch_size * sequence_length), features_shape = (current_batch_size * number_of_features, current_batch_size * number_of_features)
                                                        b = mahalanobis_right_matrix_product)

            mahalanobis_distance_flat = tf.diag_part(input = mahalanobis_distance_vectorized) # time_shape = (current_batch_size * sequence_length,), features_shape = (current_batch_size * number_of_features,)

            mahalanobis_distance_final_shaped = tf.reshape(tensor = mahalanobis_distance_flat, shape = [-1, final_shape]) # time_shape = (current_batch_size, sequence_length), features_shape = (current_batch_size, number_of_features)

            mahalanobis_distance_final_shaped_abs = tf.abs(x = mahalanobis_distance_final_shaped) # time_shape = (current_batch_size, sequence_length), features_shape = (current_batch_size, number_of_features)
            
            return mahalanobis_distance_final_shaped_abs
    
        error = Y - predictions # shape = (current_batch_size, sequence_length, number_of_features)
        absolute_error = tf.abs(x = error) # shape = (current_batch_size, sequence_length, number_of_features)
        
        with tf.variable_scope(name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
            # Time based
            absolute_error_reshaped_batch_time = tf.reshape(tensor = absolute_error,  # shape = (current_batch_size * sequence_length, number_of_features)
                                                            shape = [current_batch_size * params["sequence_length"], number_of_features])

            mahalanobis_distance_batch_time = mahalanobis_distance(error_vectors_reshaped = absolute_error_reshaped_batch_time,  # shape = (current_batch_size, sequence_length)
                                                                   mean_vector = absolute_error_mean_batch_time_variable, 
                                                                   inverse_covariance_matrix = absolute_error_inverse_covariance_matrix_batch_time_variable, 
                                                                   final_shape = params["sequence_length"])

            # Features based
            absolute_error_mapped_batch_features = tf.map_fn(fn = lambda x: tf.transpose(a = absolute_error[x, :, :]), # shape = (current_batch_size, number_of_features, sequence_length)
                                                             elems = tf.range(start = 0, limit = current_batch_size, dtype = tf.int64), 
                                                             dtype = tf.float64)

            absolute_error_reshaped_batch_features = tf.reshape(tensor = absolute_error_mapped_batch_features, # shape = (current_batch_size * number_of_features, sequence_length)
                                                                shape = [current_batch_size * number_of_features, params["sequence_length"]])

            mahalanobis_distance_batch_features = mahalanobis_distance(error_vectors_reshaped = absolute_error_reshaped_batch_features, # shape = (current_batch_size, number_of_features)
                                                                       mean_vector = absolute_error_mean_batch_features_variable, 
                                                                       inverse_covariance_matrix = absolute_error_inverse_covariance_matrix_batch_features_variable,
                                                                       final_shape = number_of_features)

        if mode != tf.estimator.ModeKeys.PREDICT:
            labels_normal_mask = tf.equal(x = labels, y = 0)
            labels_anomalous_mask = tf.equal(x = labels, y = 1)
            
            if mode == tf.estimator.ModeKeys.TRAIN:
                def update_anomaly_threshold_variables(labels_normal_mask, labels_anomalous_mask, number_of_thresholds, anomaly_thresholds, mahalanobis_distance, true_positives_at_thresholds_variable, false_negatives_at_thresholds_variable, false_positives_at_thresholds_variable, true_negatives_at_thresholds_variable):
                    mahalanobis_distance_over_thresholds = tf.map_fn(fn = lambda anomaly_threshold: mahalanobis_distance > anomaly_threshold, 
                                                                     elems = anomaly_thresholds, 
                                                                     dtype = tf.bool) # time_shape = (number_of_batch_time_anomaly_thresholds, current_batch_size, sequence_length), features_shape = (number_of_batch_features_anomaly_thresholds, current_batch_size, number_of_features)

                    mahalanobis_distance_any_over_thresholds = tf.reduce_any(input_tensor = mahalanobis_distance_over_thresholds, axis = 2) # time_shape = (number_of_batch_time_anomaly_thresholds, current_batch_size), features_shape = (number_of_batch_features_anomaly_thresholds, current_batch_size)

                    predicted_normals = tf.equal(x = mahalanobis_distance_any_over_thresholds, y = False) # time_shape = (number_of_batch_time_anomaly_thresholds, current_batch_size), features_shape = (number_of_batch_features_anomaly_thresholds, current_batch_size)
                    predicted_anomalies = tf.equal(x = mahalanobis_distance_any_over_thresholds, y = True) # time_shape = (number_of_batch_time_anomaly_thresholds, current_batch_size), features_shape = (number_of_batch_features_anomaly_thresholds, current_batch_size)

                    # Calculate confusion matrix of current batch
                    true_positives = tf.reduce_sum(input_tensor = tf.cast(x = tf.map_fn(fn = lambda threshold: tf.logical_and(x = labels_anomalous_mask, y = predicted_anomalies[threshold, :]),
                                                                                        elems = tf.range(start = 0, limit = number_of_thresholds, dtype = tf.int64),
                                                                                        dtype = tf.bool),
                                                                          dtype = tf.int64),
                                                   axis = 1) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)

                    false_negatives = tf.reduce_sum(input_tensor = tf.cast(x = tf.map_fn(fn = lambda threshold: tf.logical_and(x = labels_anomalous_mask, y = predicted_normals[threshold, :]),
                                                                                         elems = tf.range(start = 0, limit = number_of_thresholds, dtype = tf.int64),
                                                                                         dtype = tf.bool),
                                                                          dtype = tf.int64),
                                                    axis = 1) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)

                    false_positives = tf.reduce_sum(input_tensor = tf.cast(x = tf.map_fn(fn = lambda threshold: tf.logical_and(x = labels_normal_mask, y = predicted_anomalies[threshold, :]),
                                                                                         elems = tf.range(start = 0, limit = number_of_thresholds, dtype = tf.int64),
                                                                                         dtype = tf.bool),
                                                                          dtype = tf.int64),
                                                    axis = 1) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)

                    true_negatives = tf.reduce_sum(input_tensor = tf.cast(x = tf.map_fn(fn = lambda threshold: tf.logical_and(x = labels_normal_mask, y = predicted_normals[threshold, :]),
                                                                                        elems = tf.range(start = 0, limit = number_of_thresholds, dtype = tf.int64),
                                                                                        dtype = tf.bool),
                                                                          dtype = tf.int64),
                                                   axis = 1) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)

                    with tf.control_dependencies(control_inputs = [tf.assign_add(ref = true_positives_at_thresholds_variable, value = true_positives), tf.assign_add(ref = false_negatives_at_thresholds_variable, value = false_negatives), tf.assign_add(ref = false_positives_at_thresholds_variable, value = false_positives), tf.assign_add(ref = true_negatives_at_thresholds_variable, value = true_negatives)]):
                        return tf.identity(input = true_positives_at_thresholds_variable), tf.identity(input = false_negatives_at_thresholds_variable), tf.identity(input = false_positives_at_thresholds_variable), tf.identity(input = true_negatives_at_thresholds_variable)

                with tf.variable_scope(name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
                    # Time based
                    time_anomaly_thresholds = tf.linspace(start = tf.constant(value = params["min_batch_time_anomaly_threshold"], dtype = tf.float64), # shape = (number_of_batch_time_anomaly_thresholds,)
                                                          stop = tf.constant(value = params["max_batch_time_anomaly_threshold"], dtype = tf.float64), 
                                                          num = params["number_of_batch_time_anomaly_thresholds"])

                    true_positives_time_variable, false_negatives_time_variable, false_positives_time_variable, true_negatives_time_variable = \
                        update_anomaly_threshold_variables(labels_normal_mask, labels_anomalous_mask, params["number_of_batch_time_anomaly_thresholds"], time_anomaly_thresholds, mahalanobis_distance_batch_time, true_positives_at_thresholds_time_variable, false_negatives_at_thresholds_time_variable, false_positives_at_thresholds_time_variable, true_negatives_at_thresholds_time_variable)

                    # Features based
                    features_anomaly_thresholds = tf.linspace(start = tf.constant(value = params["min_batch_features_anomaly_threshold"], dtype = tf.float64), # shape = (number_of_batch_features_anomaly_thresholds,)
                                                              stop = tf.constant(value = params["max_batch_features_anomaly_threshold"], dtype = tf.float64), 
                                                              num = params["number_of_batch_features_anomaly_thresholds"])

                    true_positives_features_variable, false_negatives_features_variable, false_positives_features_variable, true_negatives_features_variable = \
                        update_anomaly_threshold_variables(labels_normal_mask, labels_anomalous_mask, params["number_of_batch_features_anomaly_thresholds"], features_anomaly_thresholds, mahalanobis_distance_batch_features, true_positives_at_thresholds_features_variable, false_negatives_at_thresholds_features_variable, false_positives_at_thresholds_features_variable, true_negatives_at_thresholds_features_variable)

                # Reconstruction loss on evaluation set
                with tf.control_dependencies(control_inputs = [true_positives_time_variable, false_negatives_time_variable, false_positives_time_variable, true_negatives_time_variable, true_positives_features_variable, false_negatives_features_variable, false_positives_features_variable, true_negatives_features_variable]):
                    def calculate_composite_classification_metrics(anomaly_thresholds, true_positives, false_negatives, false_positives, true_negatives):
                        accuracy = tf.cast(x = true_positives + true_negatives, dtype = tf.float64) / tf.cast(x = true_positives + false_negatives + false_positives + true_negatives, dtype = tf.float64) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)
                        precision = tf.cast(x = true_positives, dtype = tf.float64) / tf.cast(x = true_positives + false_positives, dtype = tf.float64) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)
                        recall = tf.cast(x = true_positives, dtype = tf.float64) / tf.cast(x = true_positives + false_negatives, dtype = tf.float64) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)
                        f_beta_score = (1 + params["f_score_beta"] ** 2) * (precision * recall) / (params["f_score_beta"] ** 2 * precision + recall) # time_shape = (number_of_batch_time_anomaly_thresholds,), features_shape = (number_of_batch_features_anomaly_thresholds,)

                        return accuracy, precision, recall, f_beta_score

                    # Time based
                    accuracy_time, precision_time, recall_time, f_beta_score_time = \
                        calculate_composite_classification_metrics(time_anomaly_thresholds, true_positives_time_variable, false_negatives_time_variable, false_positives_time_variable, true_negatives_time_variable)

                    # Features based
                    accuracy_features, precision_features, recall_features, f_beta_score_features = \
                        calculate_composite_classification_metrics(features_anomaly_thresholds, true_positives_features_variable, false_negatives_features_variable, false_positives_features_variable, true_negatives_features_variable)

                    with tf.control_dependencies(control_inputs = [precision_time, precision_features]):
                        with tf.control_dependencies(control_inputs = [recall_time, recall_features]):
                            with tf.control_dependencies(control_inputs = [f_beta_score_time, f_beta_score_features]):
                                def find_best_anomaly_threshold(anomaly_thresholds, f_beta_score, user_passed_anomaly_threshold, anomaly_threshold_variable):
                                    if user_passed_anomaly_threshold == None:
                                        best_anomaly_threshold = tf.gather(params = anomaly_thresholds, indices = tf.argmax(input = f_beta_score, axis = 0)) # shape = ()
                                    else:
                                        best_anomaly_threshold = user_passed_anomaly_threshold # shape = ()

                                    with tf.control_dependencies(control_inputs = [tf.assign(ref = anomaly_threshold_variable, value = best_anomaly_threshold)]):
                                        return tf.identity(input = anomaly_threshold_variable)
                                        
                                # Time based
                                best_anomaly_threshold_time = find_best_anomaly_threshold(time_anomaly_thresholds, f_beta_score_time, params["time_anomaly_threshold"], time_anomaly_threshold_variable)

                                # Features based
                                best_anomaly_threshold_features = find_best_anomaly_threshold(features_anomaly_thresholds, f_beta_score_features, params["features_anomaly_threshold"], features_anomaly_threshold_variable)

                                with tf.control_dependencies(control_inputs = [tf.assign(ref = time_anomaly_threshold_variable, value = best_anomaly_threshold_time), 
                                                                               tf.assign(ref = features_anomaly_threshold_variable, value = best_anomaly_threshold_features)]):
                                    loss = tf.reduce_sum(input_tensor = tf.zeros(shape = (), dtype = tf.float64) * dummy_variable)

                                    train_op = tf.contrib.layers.optimize_loss(
                                        loss = loss,
                                        global_step = tf.train.get_global_step(),
                                        learning_rate = params["learning_rate"],
                                        optimizer = "SGD")
            elif mode == tf.estimator.ModeKeys.EVAL:
                def update_anomaly_threshold_variables(labels_normal_mask, labels_anomalous_mask, anomaly_threshold, mahalanobis_distance, true_positives_at_thresholds_variable, false_negatives_at_thresholds_variable, false_positives_at_thresholds_variable, true_negatives_at_thresholds_variable):
                    mahalanobis_distance_over_threshold  = mahalanobis_distance > anomaly_threshold # time_shape = (current_batch_size, sequence_length), features_shape = (current_batch_size, number_of_features)

                    mahalanobis_distance_any_over_threshold = tf.reduce_any(input_tensor = mahalanobis_distance_over_threshold, axis = -1) # time_shape = (current_batch_size,), features_shape = (current_batch_size,)

                    predicted_normals = tf.equal(x = mahalanobis_distance_any_over_threshold, y = False) # time_shape = (current_batch_size,), features_shape = (current_batch_size,)
                    predicted_anomalies = tf.equal(x = mahalanobis_distance_any_over_threshold, y = True) # time_shape = (current_batch_size,), features_shape = (current_batch_size,)

                    # Calculate confusion matrix of current batch
                    true_positives = tf.reduce_sum(input_tensor = tf.cast(x = tf.logical_and(x = labels_anomalous_mask, y = predicted_anomalies), dtype = tf.int64),
                                                   axis = -1) # time_shape = (), features_shape = ()

                    false_negatives = tf.reduce_sum(input_tensor = tf.cast(x = tf.logical_and(x = labels_anomalous_mask, y = predicted_normals), dtype = tf.int64),
                                                    axis = -1) # time_shape = (), features_shape = ()

                    false_positives = tf.reduce_sum(input_tensor = tf.cast(x = tf.logical_and(x = labels_normal_mask, y = predicted_anomalies), dtype = tf.int64),
                                                    axis = -1) # time_shape = (), features_shape = ()

                    true_negatives = tf.reduce_sum(input_tensor = tf.cast(x = tf.logical_and(x = labels_normal_mask, y = predicted_normals), dtype = tf.int64),
                                                   axis = -1) # time_shape = (), features_shape = ()

                    with tf.control_dependencies(control_inputs = [tf.assign_add(ref = true_positives_at_thresholds_variable, value = true_positives), tf.assign_add(ref = false_negatives_at_thresholds_variable, value = false_negatives), tf.assign_add(ref = false_positives_at_thresholds_variable, value = false_positives), tf.assign_add(ref = true_negatives_at_thresholds_variable, value = true_negatives)]):
                        return tf.identity(input = true_positives_at_thresholds_variable), tf.identity(input = false_negatives_at_thresholds_variable), tf.identity(input = false_positives_at_thresholds_variable), tf.identity(input = true_negatives_at_thresholds_variable)
                    
                with tf.variable_scope(name_or_scope = "anomaly_threshold_eval_variables", reuse = tf.AUTO_REUSE):
                    # Time based
                    true_positives_time_variable, false_negatives_time_variable, false_positives_time_variable, true_negatives_time_variable = \
                        update_anomaly_threshold_variables(labels_normal_mask, labels_anomalous_mask, time_anomaly_threshold_variable, mahalanobis_distance_batch_time, true_positives_at_threshold_eval_time_variable, false_negatives_at_threshold_eval_time_variable, false_positives_at_threshold_eval_time_variable, true_negatives_at_threshold_eval_time_variable)

                    # Features based
                    true_positives_features_variable, false_negatives_features_variable, false_positives_features_variable, true_negatives_features_variable = \
                        update_anomaly_threshold_variables(labels_normal_mask, labels_anomalous_mask, features_anomaly_threshold_variable, mahalanobis_distance_batch_features, true_positives_at_threshold_eval_features_variable, false_negatives_at_threshold_eval_features_variable, false_positives_at_threshold_eval_features_variable, true_negatives_at_threshold_eval_features_variable)
                    
                with tf.control_dependencies(control_inputs = [true_positives_time_variable, false_negatives_time_variable, false_positives_time_variable, true_negatives_time_variable, true_positives_features_variable, false_negatives_features_variable, false_positives_features_variable, true_negatives_features_variable]):
                    def calculate_composite_classification_metrics(anomaly_thresholds, true_positives, false_negatives, false_positives, true_negatives, accuracy_at_threshold_variable, precision_at_threshold_variable, recall_at_threshold_variable, f_beta_score_at_threshold_variable):
                        accuracy = tf.cast(x = true_positives + true_negatives, dtype = tf.float64) / tf.cast(x = true_positives + false_negatives + false_positives + true_negatives, dtype = tf.float64) # shape = ()
                        precision = tf.cast(x = true_positives, dtype = tf.float64) / tf.cast(x = true_positives + false_positives, dtype = tf.float64) # shape = ()
                        recall = tf.cast(x = true_positives, dtype = tf.float64) / tf.cast(x = true_positives + false_negatives, dtype = tf.float64) # shape = ()
                        f_beta_score = (1 + params["f_score_beta"] ** 2) * (precision * recall) / (params["f_score_beta"] ** 2 * precision + recall) # shape = ()

                        with tf.control_dependencies(control_inputs = [tf.assign(ref = accuracy_at_threshold_variable, value = accuracy), tf.assign(ref = precision_at_threshold_variable, value = precision), tf.assign(ref = recall_at_threshold_variable, value = recall)]):
                            with tf.control_dependencies(control_inputs = [tf.assign(ref = f_beta_score_at_threshold_variable, value = f_beta_score)]):
                                return tf.identity(input = accuracy_at_threshold_variable), tf.identity(input = precision_at_threshold_variable), tf.identity(input = recall_at_threshold_variable), tf.identity(input = f_beta_score_at_threshold_variable)

                    with tf.variable_scope(name_or_scope = "anomaly_threshold_eval_variables", reuse = tf.AUTO_REUSE):
                        # Time based
                        accuracy_time, precision_time, recall_time, f_beta_score_time = \
                            calculate_composite_classification_metrics(time_anomaly_threshold_variable, true_positives_time_variable, false_negatives_time_variable, false_positives_time_variable, true_negatives_time_variable, accuracy_at_threshold_eval_time_variable, precision_at_threshold_eval_time_variable, recall_at_threshold_eval_time_variable, f_beta_score_at_threshold_eval_time_variable)

                        # Features based
                        accuracy_features, precision_features, recall_features, f_beta_score_features = \
                            calculate_composite_classification_metrics(features_anomaly_threshold_variable, true_positives_features_variable, false_negatives_features_variable, false_positives_features_variable, true_negatives_features_variable, accuracy_at_threshold_eval_features_variable, precision_at_threshold_eval_features_variable, recall_at_threshold_eval_features_variable, f_beta_score_at_threshold_eval_features_variable)

                    with tf.control_dependencies(control_inputs = [accuracy_time, precision_time, recall_time, f_beta_score_time, accuracy_features, precision_features, recall_features, f_beta_score_features]):
                        loss = tf.losses.mean_squared_error(labels = Y, predictions = predictions)

                        # Anomaly detection eval metrics
                        eval_metric_ops = {
                            # Time based
                            "time_anomaly_true_positives": tuple([true_positives_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.int64)]),
                            "time_anomaly_false_negatives": tuple([false_negatives_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.int64)]),
                            "time_anomaly_false_positives": tuple([false_positives_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.int64)]),
                            "time_anomaly_true_negatives": tuple([true_negatives_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.int64)]),

                            "time_anomaly_accuracy": tuple([accuracy_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.float64)]),
                            "time_anomaly_precision": tuple([precision_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.float64)]),
                            "time_anomaly_recall": tuple([recall_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.float64)]),
                            "time_anomaly_f_beta_score": tuple([f_beta_score_at_threshold_eval_time_variable, tf.zeros(shape = [], dtype = tf.float64)]),

                             # Features based
                            "features_anomaly_true_positives": tuple([true_positives_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.int64)]),
                            "features_anomaly_false_negatives": tuple([false_negatives_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.int64)]),
                            "features_anomaly_false_positives": tuple([false_positives_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.int64)]),
                            "features_anomaly_true_negatives": tuple([true_negatives_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.int64)]),

                            "features_anomaly_accuracy": tuple([accuracy_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.float64)]),
                            "features_anomaly_precision": tuple([precision_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.float64)]),
                            "features_anomaly_recall": tuple([recall_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.float64)]),
                            "features_anomaly_f_beta_score": tuple([f_beta_score_at_threshold_eval_features_variable, tf.zeros(shape = [], dtype = tf.float64)])
                        }
        else: # mode == tf.estimator.ModeKeys.PREDICT
            # Flag predictions as either normal or anomalous
            batch_time_anomaly_flags = tf.where(condition = tf.reduce_any(input_tensor = tf.greater(x = tf.abs(x = mahalanobis_distance_batch_time), # shape = (current_batch_size,)
                                                                                                    y = time_anomaly_threshold_variable), 
                                                                          axis = 1), 
                                                x = tf.ones(shape = [current_batch_size], dtype = tf.int64), 
                                                y = tf.zeros(shape = [current_batch_size], dtype = tf.int64))

            batch_features_anomaly_flags = tf.where(condition = tf.reduce_any(input_tensor = tf.greater(x = tf.abs(x = mahalanobis_distance_batch_features), # shape = (current_batch_size,)
                                                                                                        y = features_anomaly_threshold_variable), 
                                                                              axis = 1), 
                                                    x = tf.ones(shape = [current_batch_size], dtype = tf.int64), 
                                                    y = tf.zeros(shape = [current_batch_size], dtype = tf.int64))
        
            # Create predictions dictionary
            predictions_dict = {"Y": Y,
                                "predictions": predictions, 
                                "error": error,
                                "absolute_error": absolute_error,
                                "mahalanobis_distance_batch_time": mahalanobis_distance_batch_time, 
                                "mahalanobis_distance_batch_features": mahalanobis_distance_batch_features, 
                                "batch_time_anomaly_flags": batch_time_anomaly_flags, 
                                "batch_features_anomaly_flags": batch_features_anomaly_flags}

            # Create export outputs
            export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs = predictions_dict)}

    # Return EstimatorSpec
    return tf.estimator.EstimatorSpec(
        mode = mode,
        predictions = predictions_dict,
        loss = loss,
        train_op = train_op,
        eval_metric_ops = eval_metric_ops,
        export_outputs = export_outputs)

# Create our serving input function to accept the data at serving and send it in the right format to our custom estimator
def serving_input_fn(sequence_length):
    # This function fixes the shape and type of our input strings
    def fix_shape_and_type_for_serving(placeholder):
        current_batch_size = tf.shape(input = placeholder, out_type = tf.int64)[0]
        
        # String split each string in the batch and output the values from the resulting SparseTensors
        split_string = tf.stack(values = tf.map_fn( # shape = (batch_size, sequence_length)
            fn = lambda x: tf.string_split(source = [placeholder[x]], delimiter = ',').values, 
            elems = tf.range(start = 0, limit = current_batch_size, dtype = tf.int64), 
            dtype = tf.string), axis = 0)
        
        # Convert each string in the split tensor to float
        feature_tensor = tf.string_to_number(string_tensor = split_string, out_type = tf.float64) # shape = (batch_size, sequence_length)
        
        return feature_tensor
    
    # This function fixes dynamic shape ambiguity of last dimension so that we will be able to use it in our DNN (since tf.layers.dense require the last dimension to be known)
    def get_shape_and_set_modified_shape_2D(tensor, additional_dimension_sizes):
        # Get static shape for tensor and convert it to list
        shape = tensor.get_shape().as_list()
        # Set outer shape to additional_dimension_sizes[0] since we know that this is the correct size
        shape[1] = additional_dimension_sizes[0]
        # Set the shape of tensor to our modified shape
        tensor.set_shape(shape = shape) # shape = (batch_size, additional_dimension_sizes[0])

        return tensor
            
    # Create placeholders to accept the data sent to the model at serving time
    feature_placeholders = { # all features come in as a batch of strings, shape = (batch_size,), this was so because of passing the arrays to online ml-engine prediction
        feature: tf.placeholder(dtype = tf.string, shape = [None]) for feature in UNLABELED_CSV_COLUMNS
    }
    
    # Create feature tensors
    features = {key: fix_shape_and_type_for_serving(placeholder = tensor) for key, tensor in feature_placeholders.items()}
    
    # Fix dynamic shape ambiguity of feature tensors for our DNN
    features = {key: get_shape_and_set_modified_shape_2D(tensor = tensor, additional_dimension_sizes = [sequence_length]) for key, tensor in features.items()}

    return tf.estimator.export.ServingInputReceiver(features = features, receiver_tensors = feature_placeholders)

# Create estimator to train and evaluate
def train_and_evaluate(args):
    # Create our custom estimator using our model function
    estimator = tf.estimator.Estimator(
        model_fn = lstm_encoder_decoder_autoencoder_anomaly_detection,
        model_dir = args["output_dir"],
        params = {
            "sequence_length": args["sequence_length"],
            "reverse_labels_sequence": args["reverse_labels_sequence"],
            "encoder_lstm_hidden_units": args["encoder_lstm_hidden_units"],
            "decoder_lstm_hidden_units": args["decoder_lstm_hidden_units"],
            "lstm_dropout_output_keep_probs": args["lstm_dropout_output_keep_probs"], 
            "dnn_hidden_units": args["dnn_hidden_units"], 
            "learning_rate": args["learning_rate"],
            "evaluation_mode": args["evaluation_mode"],
            "number_of_batch_time_anomaly_thresholds": args["number_of_batch_time_anomaly_thresholds"],
            "number_of_batch_features_anomaly_thresholds": args["number_of_batch_features_anomaly_thresholds"],
            "min_batch_time_anomaly_threshold": args["min_batch_time_anomaly_threshold"],
            "max_batch_time_anomaly_threshold": args["max_batch_time_anomaly_threshold"],
            "min_batch_features_anomaly_threshold": args["min_batch_features_anomaly_threshold"],
            "max_batch_features_anomaly_threshold": args["max_batch_features_anomaly_threshold"],
            "time_anomaly_threshold": args["time_anomaly_threshold"], 
            "features_anomaly_threshold": args["features_anomaly_threshold"],
            "eps": args["eps"],
            "f_score_beta": args["f_score_beta"]})
    
    if args["evaluation_mode"] == "reconstruction":
        early_stopping_hook = tf.contrib.estimator.stop_if_no_decrease_hook(
            estimator = estimator,
            metric_name = "rmse",
            max_steps_without_decrease = 100,
            min_steps = 1000,
            run_every_secs = 60,
            run_every_steps = None)

        # Create train spec to read in our training data
        train_spec = tf.estimator.TrainSpec(
            input_fn = read_dataset(
                filename = args["train_file_pattern"],
                mode = tf.estimator.ModeKeys.TRAIN, 
                batch_size = args["train_batch_size"],
                params = args),
            max_steps = args["train_steps"], 
            hooks = [early_stopping_hook])

        # Create eval spec to read in our validation data and export our model
        eval_spec = tf.estimator.EvalSpec(
            input_fn = read_dataset(
                filename = args["eval_file_pattern"], 
                mode = tf.estimator.ModeKeys.EVAL, 
                batch_size = args["eval_batch_size"],
                params = args),
            steps = None,
            start_delay_secs = args["start_delay_secs"], # start evaluating after N seconds
            throttle_secs = args["throttle_secs"])    # evaluate every N seconds

        # Create train and evaluate loop to train and evaluate our estimator
        tf.estimator.train_and_evaluate(estimator = estimator, train_spec = train_spec, eval_spec = eval_spec)
    else:
        if args["evaluation_mode"] == "calculate_error_distribution_statistics":
            # Get final mahalanobis statistics over the entire validation_1 dataset
            train_spec = tf.estimator.TrainSpec(
                input_fn = read_dataset(
                    filename = args["train_file_pattern"],
                    mode = tf.estimator.ModeKeys.EVAL, # only read through validation dataset once
                    batch_size = args["train_batch_size"],
                    params = args),
                max_steps = args["train_steps"])

            # Don't create exporter for serving yet since anomaly thresholds aren't trained yet
            exporter = None
        elif args["evaluation_mode"] == "tune_anomaly_thresholds":
            # Tune anomaly thresholds using valdiation_2 and validation_anomaly datasets
            train_spec = tf.estimator.TrainSpec(
                input_fn = read_dataset(
                    filename = args["train_file_pattern"],
                    mode = tf.estimator.ModeKeys.EVAL, # only read through validation dataset once
                    batch_size = args["train_batch_size"],
                    params = args),
                max_steps = args["train_steps"])
            
            # Create exporter that uses serving_input_fn to create saved_model for serving
            exporter = tf.estimator.LatestExporter(name = "exporter", serving_input_receiver_fn = lambda: serving_input_fn(args["sequence_length"]))

        # Create eval spec to read in our validation data and export our model
        eval_spec = tf.estimator.EvalSpec(
            input_fn = read_dataset(
                filename = args["eval_file_pattern"], 
                mode = tf.estimator.ModeKeys.EVAL, 
                batch_size = args["eval_batch_size"],
                params = args),
            steps = None,
            exporters = exporter,
            start_delay_secs = args["start_delay_secs"], # start evaluating after N seconds
            throttle_secs = args["throttle_secs"])    # evaluate every N seconds
        
        # Create train and evaluate loop to train and evaluate our estimator
        tf.estimator.train_and_evaluate(estimator = estimator, train_spec = train_spec, eval_spec = eval_spec)
