import tensorflow as tf


# LSTM Encoder-decoder Autoencoder model functions
def create_LSTM_stack(lstm_hidden_units, lstm_dropout_output_keep_probs):
  """Create LSTM stacked cells.

  Given list of LSTM hidden units and list of LSTM dropout output keep
  probabilities.

  Args:
    lstm_hidden_units: List of integers for the number of hidden units in each
      layer.
    lstm_dropout_output_keep_probs: List of floats for the dropout output keep
      probabilities for each layer.

  Returns:
    MultiRNNCell object of stacked LSTM layers.
  """
  # First create a list of LSTM cell objects using our list of lstm hidden
  # unit sizes
  lstm_cells = [tf.contrib.rnn.BasicLSTMCell(
      num_units=units,
      forget_bias=1.0,
      state_is_tuple=True)
                for units in lstm_hidden_units]

  # Next apply a dropout wrapper to our stack of LSTM cells,
  # in this case just on the outputs
  dropout_lstm_cells = [tf.nn.rnn_cell.DropoutWrapper(
      cell=lstm_cells[cell_index],
      input_keep_prob=1.0,
      output_keep_prob=lstm_dropout_output_keep_probs[cell_index],
      state_keep_prob=1.0)
                        for cell_index in range(len(lstm_cells))]

  # Create a stack of layers of LSTM cells
  # Combines list into MultiRNNCell object
  stacked_lstm_cells = tf.contrib.rnn.MultiRNNCell(
      cells=dropout_lstm_cells,
      state_is_tuple=True)

  return stacked_lstm_cells


# The rnn_decoder function takes labels during TRAIN/EVAL
# and a start token followed by its previous predictions during PREDICT
# Starts with an initial state of the final encoder states
def rnn_decoder(dec_input, init_state, cell, infer, dnn_hidden_units, num_feat):
  """Decoder for RNN cell.

  Given list of LSTM hidden units and list of LSTM dropout output keep
  probabilities.

  Args:
    dec_input: List of tf.float64 current batch size by number of features
      matrix tensors input to the decoder.
    init_state: Initial state of the decoder cell. Final state from the
      encoder cell.
    cell: RNN Cell object.
    infer: Boolean whether in inference mode or not.
    dnn_hidden_units: Python list of integers of number of units per DNN layer.
    num_feat: Python integer of the number of features.

  Returns:
    outputs: List of decoder outputs of length number of timesteps of tf.float64
      current batch size by number of features matrix tensors.
    state: Final cell state of the decoder.
  """
  # Create the decoder variable scope
  with tf.variable_scope("decoder"):
    # Load in our initial state from our encoder
    # Tuple of final encoder c_state and h_state of final encoder layer
    state = init_state

    # Create an empty list to store our hidden state output for every timestep
    outputs = []

    # Begin with no previous output
    previous_output = None

    # Loop over all of our dec_input which will be seq_len long
    for index, decoder_input in enumerate(dec_input):
      # If there has been a previous output, we will determine the next input
      if previous_output is not None:
        # Create the input layer to our DNN
        # shape = (cur_batch_size, lstm_hidden_units[-1])
        network = previous_output

        # Create our dnn variable scope
        with tf.variable_scope(name_or_scope="dnn", reuse=tf.AUTO_REUSE):
          # Add hidden layers with the given number of units/neurons per layer
          # shape = (cur_batch_size, dnn_hidden_units[i])
          for units in dnn_hidden_units:
            network = tf.layers.dense(
                inputs=network,
                units=units,
                activation=tf.nn.relu)

          # Connect final hidden layer to linear layer to get the logits
          # shape = (cur_batch_size, num_feat)
          logits = tf.layers.dense(
              inputs=network,
              units=num_feat,
              activation=None)

        # If we are in inference then we will overwrite our next decoder_input
        # with the logits we just calculated. Otherwise, we leave the decoder
        # input input as it was from the enumerated list. We have to calculate
        # the logits even when not using them so that the correct DNN subgraph
        # will be generated here and after the encoder-decoder for both
        # training and inference
        if infer:
          # shape = (cur_batch_size, num_feat)
          decoder_input = logits

      # If this isn"t our first time through the loop, just reuse(share) the
      # same variables for each iteration within the current variable scope
      if index > 0:
        tf.get_variable_scope().reuse_variables()

      # Run the decoder input through the decoder stack picking up from the
      # previous state
      # output_shape = (cur_batch_size, lstm_hidden_units[-1])
      # state_shape = # tuple of final decoder c_state and h_state
      output, state = cell(decoder_input, state)

      # Append the current decoder hidden state output to the outputs list
      # List seq_len long of shape = (cur_batch_size, lstm_hidden_units[-1])
      outputs.append(output)

      # Set the previous output to the output just calculated
      # shape = (cur_batch_size, lstm_hidden_units[-1])
      previous_output = output
  return outputs, state


def lstm_enc_dec_autoencoder_model(
    X, mode, params, cur_batch_size, dummy_var):
  """LSTM autoencoder to reconstruct inputs and minimize reconstruction error.

  Given data matrix tensor X, the current Estimator mode, the dictionary of
  parameters, current batch size, and the number of features, process through
  LSTM model encoder, decoder, and DNN subgraphs and return reconstructed inputs
  as output.

  Args:
    X: tf.float64 matrix tensor of input data.
    mode: Estimator ModeKeys. Can take values of TRAIN, EVAL, and PREDICT.
    params: Dictionary of parameters.
    cur_batch_size: Current batch size, could be partially filled.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: Reconstruction loss.
    train_op: Train operation so that Estimator can correctly add to dependency
      graph.
    X_time: 2D tensor representation of time major input data.
    X_time_recon: 2D tensor representation of time major input data.
    X_feat: 2D tensor representation of feature major input data.
    X_feat_recon: 2D tensor representation of feature major input data.
  """
  # Unstack 3-D features tensor into a sequence(list) of 2-D tensors
  # shape = (cur_batch_size, num_feat)
  X_sequence = tf.unstack(value=X, num=params["seq_len"], axis=1)

  # Since this is an autoencoder, the features are the labels.
  # It often works better though to have the labels in reverse order
  # shape = (cur_batch_size, seq_len, num_feat)
  if params["reverse_labels_sequence"]:
    Y = tf.reverse_sequence(
        input=X,
        seq_lengths=tf.tile(
            input=tf.constant(value=[params["seq_len"]], dtype=tf.int64),
            multiples=tf.expand_dims(input=cur_batch_size, axis=0)),
        seq_axis=1,
        batch_axis=0)
  else:
    Y = X  # shape = (cur_batch_size, seq_len, num_feat)

  ##############################################################################

  # Create encoder of encoder-decoder LSTM stacks

  # Create our decoder now
  dec_stacked_lstm_cells = create_LSTM_stack(
      params["dec_lstm_hidden_units"],
      params["lstm_dropout_output_keep_probs"])

  # Create the encoder variable scope
  with tf.variable_scope("encoder"):
    # Create separate encoder cells with their own weights separate from decoder
    enc_stacked_lstm_cells = create_LSTM_stack(
        params["enc_lstm_hidden_units"],
        params["lstm_dropout_output_keep_probs"])

    # Encode the input sequence using our encoder stack of LSTMs
    # enc_outputs = seq_len long of shape = (cur_batch_size, enc_lstm_hidden_units[-1])
    # enc_states = tuple of final encoder c_state and h_state for each layer
    _, enc_states = tf.nn.static_rnn(
        cell=enc_stacked_lstm_cells,
        inputs=X_sequence,
        initial_state=enc_stacked_lstm_cells.zero_state(
            batch_size=tf.cast(x=cur_batch_size, dtype=tf.int32),
            dtype=tf.float64),
        dtype=tf.float64)

    # We just pass on the final c and h states of the encoder"s last layer,
    # so extract that and drop the others
    # LSTMStateTuple shape = (cur_batch_size, lstm_hidden_units[-1])
    enc_final_states = enc_states[-1]

    # Extract the c and h states from the tuple
    # both have shape = (cur_batch_size, lstm_hidden_units[-1])
    enc_final_c, enc_final_h = enc_final_states

    # In case the decoder"s first layer's number of units is different than
    # encoder's last layer's number of units, use a dense layer to map to the
    # correct shape
    # shape = (cur_batch_size, dec_lstm_hidden_units[0])
    enc_final_c_dense = tf.layers.dense(
        inputs=enc_final_c,
        units=params["dec_lstm_hidden_units"][0],
        activation=None)

    # shape = (cur_batch_size, dec_lstm_hidden_units[0])
    enc_final_h_dense = tf.layers.dense(
        inputs=enc_final_h,
        units=params["dec_lstm_hidden_units"][0],
        activation=None)

    # The decoder"s first layer"s state comes from the encoder,
    # the rest of the layers" initial states are zero
    dec_init_states = tuple(
        [tf.contrib.rnn.LSTMStateTuple(c=enc_final_c_dense,
                                       h=enc_final_h_dense)] + \
        [tf.contrib.rnn.LSTMStateTuple(
            c=tf.zeros(shape=[cur_batch_size, units], dtype=tf.float64),
            h=tf.zeros(shape=[cur_batch_size, units], dtype=tf.float64))
         for units in params["dec_lstm_hidden_units"][1:]])

  ##############################################################################

  # Create decoder of encoder-decoder LSTM stacks

  # Train our decoder now

  # Encoder-decoders work differently during training, evaluation, and inference
  # so we will have two separate subgraphs for each
  if (mode == tf.estimator.ModeKeys.TRAIN and
      params["training_mode"] == "reconstruction"):
    # Break 3-D labels tensor into a list of 2-D tensors
    # shape = (cur_batch_size, num_feat)
    unstacked_labels = tf.unstack(value=Y, num=params["seq_len"], axis=1)

    # Call our decoder using the labels as our inputs, the encoder final state
    # as our initial state, our other LSTM stack as our cells, and inference
    # set to false
    dec_outputs, _ = rnn_decoder(
        dec_input=unstacked_labels,
        init_state=dec_init_states,
        cell=dec_stacked_lstm_cells,
        infer=False,
        dnn_hidden_units=params["dnn_hidden_units"],
        num_feat=params["num_feat"])
  else:
    # Since this is inference create fake labels. The list length needs to be
    # the output sequence length even though only the first element is the only
    # one actually used (as our go signal)
    fake_labels = [tf.zeros(shape=[cur_batch_size, params["num_feat"]],
                            dtype=tf.float64)
                   for _ in range(params["seq_len"])]

    # Call our decoder using fake labels as our inputs, the encoder final state
    # as our initial state, our other LSTM stack as our cells, and inference
    # set to true
    # dec_outputs = seq_len long of shape = (cur_batch_size, dec_lstm_hidden_units[-1])
    # decoder_states = tuple of final decoder c_state and h_state for each layer
    dec_outputs, _ = rnn_decoder(
        dec_input=fake_labels,
        init_state=dec_init_states,
        cell=dec_stacked_lstm_cells,
        infer=True,
        dnn_hidden_units=params["dnn_hidden_units"],
        num_feat=params["num_feat"])

  # Stack together list of rank 2 decoder output tensors into one rank 3 tensor
  # shape = (cur_batch_size, seq_len, lstm_hidden_units[-1])
  stacked_dec_outputs = tf.stack(values=dec_outputs, axis=1)

  # Reshape rank 3 decoder outputs into rank 2 by folding sequence length into
  # batch size
  # shape = (cur_batch_size * seq_len, lstm_hidden_units[-1])
  reshaped_stacked_dec_outputs = tf.reshape(
      tensor=stacked_dec_outputs,
      shape=[cur_batch_size * params["seq_len"],
             params["dec_lstm_hidden_units"][-1]])

  ##############################################################################

  # Create the DNN structure now after the encoder-decoder LSTM stack
  # Create the input layer to our DNN
  # shape = (cur_batch_size * seq_len, lstm_hidden_units[-1])
  network = reshaped_stacked_dec_outputs

  # Reuse the same variable scope as we used within our decoder (for inference)
  with tf.variable_scope(name_or_scope="dnn", reuse=tf.AUTO_REUSE):
    # Add hidden layers with the given number of units/neurons per layer
    for units in params["dnn_hidden_units"]:
      # shape = (cur_batch_size * seq_len, dnn_hidden_units[i])
      network = tf.layers.dense(
          inputs=network,
          units=units,
          activation=tf.nn.relu)

    # Connect the final hidden layer to a dense layer with no activation to
    # get the logits
    # shape = (cur_batch_size * seq_len, num_feat)
    logits = tf.layers.dense(
        inputs=network,
        units=params["num_feat"],
        activation=None)

  # Now that we are through the final DNN for each sequence element for
  # each example in the batch, reshape the predictions to match our labels.
  # shape = (cur_batch_size, seq_len, num_feat)
  predictions = tf.reshape(
      tensor=logits,
      shape=[cur_batch_size, params["seq_len"], params["num_feat"]])

  if (mode == tf.estimator.ModeKeys.TRAIN and
      params["training_mode"] == "reconstruction"):
    loss = tf.losses.mean_squared_error(labels=Y, predictions=predictions)

    train_op = tf.contrib.layers.optimize_loss(
        loss=loss,
        global_step=tf.train.get_global_step(),
        learning_rate=params["learning_rate"],
        optimizer="Adam")

    return loss, train_op, None, None, None, None
  else:
    if params["reverse_labels_sequence"]:
      # shape=(cur_batch_size, seq_len, num_feat)
      predictions = tf.reverse_sequence(
          input=predictions,
          seq_lengths=tf.tile(
              input=tf.constant(value=[params["seq_len"]], dtype=tf.int64),
              multiples=tf.expand_dims(input=cur_batch_size, axis=0)),
          seq_axis=1,
          batch_axis=0)

    # Reshape into 2-D tensors
    # Time based
    # shape = (cur_batch_size * seq_len, num_feat)
    X_time = tf.reshape(
        tensor=X,
        shape=[cur_batch_size * params["seq_len"], params["num_feat"]])

    X_time_recon = tf.reshape(
        tensor=predictions,
        shape=[cur_batch_size * params["seq_len"], params["num_feat"]])

    # Features based
    # shape = (cur_batch_size, num_feat, seq_len)
    X_transposed = tf.transpose(a=X, perm=[0, 2, 1])

    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat = tf.reshape(
        tensor=X_transposed,
        shape=[cur_batch_size * params["num_feat"], params["seq_len"]])

    # shape = (cur_batch_size, num_feat, seq_len)
    predictions_transposed = tf.transpose(a=predictions, perm=[0, 2, 1])

    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat_recon = tf.reshape(
        tensor=predictions_transposed,
        shape=[cur_batch_size * params["num_feat"], params["seq_len"]])

    return None, None, X_time, X_time_recon, X_feat, X_feat_recon
