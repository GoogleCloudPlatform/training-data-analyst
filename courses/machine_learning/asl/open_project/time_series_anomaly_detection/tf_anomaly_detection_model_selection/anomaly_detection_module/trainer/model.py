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


# Input function functions
def split_and_convert_string(string_tensor):
  """Splits and converts string tensor into dense float tensor.

  Given string tensor, splits string by delimiter, converts to and returns
  dense float tensor.

  Args:
    string_tensor: tf.string tensor.

  Returns:
    tf.float64 tensor split along delimiter.
  """
  # Split string tensor into a sparse tensor based on delimiter
  split_string = tf.string_split(source=tf.expand_dims(
      input=string_tensor, axis=0), delimiter=",")

  # Converts the values of the sparse tensor to floats
  converted_tensor = tf.string_to_number(
      string_tensor=split_string.values,
      out_type=tf.float64)

  # Create a new sparse tensor with the new converted values,
  # because the original sparse tensor values are immutable
  new_sparse_tensor = tf.SparseTensor(
      indices=split_string.indices,
      values=converted_tensor,
      dense_shape=split_string.dense_shape)

  # Create a dense tensor of the float values that were converted from text csv
  dense_floats = tf.sparse_tensor_to_dense(
      sp_input=new_sparse_tensor, default_value=0.0)

  dense_floats_vector = tf.squeeze(input=dense_floats, axis=0)

  return dense_floats_vector


def convert_sequences_from_strings_to_floats(features, column_list, seq_len):
  """Converts sequences from single strings to a sequence of floats.

  Given features dictionary and feature column names list, convert features
  from strings to a sequence of floats.

  Args:
    features: Dictionary of tensors of our features as tf.strings.
    column_list: List of column names of our features.
    seq_len: Number of timesteps in sequence.

  Returns:
    Dictionary of tensors of our features as tf.float64s.
  """
  for column in column_list:
    features[column] = split_and_convert_string(features[column])
    # Since we know the sequence length, set the shape to remove the ambiguity
    features[column].set_shape([seq_len])

  return features


def decode_csv(value_column, mode, seq_len, training_mode, labeled_tune_thresh):
  """Decodes CSV file into tensors.

  Given single string tensor and sequence length, returns features dictionary
  of tensors and labels tensor.

  Args:
    value_column: tf.string tensor of shape () compromising entire line of
      CSV file.
    mode: The estimator ModeKeys. Can be TRAIN or EVAL.
    seq_len: Number of timesteps in sequence.
    training_mode: Which training mode we're in. Values are "reconstruction",
      "calculate_error_distribution_statistics", and "tune_anomaly_thresholds".
    labeled_tune_thresh: If tune anomaly thresholds dataset is labeled or not.

  Returns:
    Features dictionary of tensors and labels tensor.
  """
  if (mode == tf.estimator.ModeKeys.TRAIN or
      (mode == tf.estimator.ModeKeys.EVAL and
       (training_mode != "tune_anomaly_thresholds" or
        (training_mode == "tune_anomaly_thresholds" and
         not labeled_tune_thresh)))):
    # For subset of CSV files that do NOT have labels
    columns = tf.decode_csv(
        records=value_column,
        record_defaults=UNLABELED_DEFAULTS,
        field_delim=";")

    features = dict(zip(UNLABELED_CSV_COLUMNS, columns))
    features = convert_sequences_from_strings_to_floats(
        features=features, column_list=UNLABELED_CSV_COLUMNS, seq_len=seq_len)
    return features
  else:
    # For subset of CSV files that DO have labels
    columns = tf.decode_csv(
        records=value_column,
        record_defaults=LABELED_DEFAULTS,
        field_delim=";")

    features = dict(zip(LABELED_CSV_COLUMNS, columns))

    labels = tf.cast(x=features.pop(LABEL_COLUMN), dtype=tf.float64)

    features = convert_sequences_from_strings_to_floats(
        features=features,
        column_list=UNLABELED_CSV_COLUMNS,
        seq_len=seq_len)

    return features, labels


def read_dataset(filename, mode, batch_size, params):
  """Reads CSV time series dataset using tf.data, doing necessary preprocessing.

  Given filename, mode, batch size and other parameters, read CSV dataset using
  Dataset API, apply necessary preprocessing, and return an input function to
  the Estimator API.

  Args:
    filename: The file pattern that we want to read into our tf.data dataset.
    mode: The estimator ModeKeys. Can be TRAIN or EVAL.
    batch_size: Number of examples to read and combine into a single tensor.
    params: Additional parameters.

  Returns:
    An input function.
  """
  def _input_fn():
    """Wrapper input function to be used by Estimator API to get data tensors.

    Returns:
      Batched dataset object of dictionary of feature tensors and label tensor.
    """

    # Create list of files that match pattern
    file_list = tf.gfile.Glob(filename=filename)

    # Create dataset from file list
    dataset = tf.data.TextLineDataset(filenames=file_list)  # Read text file

    # Decode the CSV file into a features dictionary of tensors
    dataset = dataset.map(
        map_func=lambda x: decode_csv(
            value_column=x,
            mode=mode,
            seq_len=params["seq_len"],
            training_mode=params["training_mode"]))

    # Determine amount of times to repeat file if we are training or evaluating
    if mode == tf.estimator.ModeKeys.TRAIN:
      num_epochs = None  # indefinitely
    else:
      num_epochs = 1  # end-of-input after this

    # Repeat files num_epoch times
    dataset = dataset.repeat(count=num_epochs)

    # Group the data into batches
    dataset = dataset.batch(batch_size=batch_size)

    # Determine if we should shuffle based on if we are training or evaluating
    if mode == tf.estimator.ModeKeys.TRAIN:
      dataset = dataset.shuffle(buffer_size=10 * batch_size)

    # Create a iterator, then pull batch of features from the example queue
    batched_dataset = dataset.make_one_shot_iterator().get_next()

    return batched_dataset

  return _input_fn


# Dense autoencoder model functions
def dense_encoder(X, params):
  """Dense model encoder subgraph that produces latent matrix.

  Given data matrix tensor X and dictionary of parameters, process through dense
  model encoder subgraph and return encoder latent vector for each example in
  batch.

  Args:
    X: tf.float64 matrix tensor of input data.
    params: Dictionary of parameters.

  Returns:
    tf.float64 matrix tensor encoder latent vector for each example in batch.
  """
  # Create the input layer to our DNN
  network = X

  # Add hidden layers with the given number of units/neurons per layer
  for units in params["enc_dnn_hidden_units"]:
    network = tf.layers.dense(
        inputs=network,
        units=units,
        activation=tf.nn.relu)

  latent_matrix = tf.layers.dense(
      inputs=network,
      units=params["latent_vector_size"],
      activation=tf.nn.relu)

  return latent_matrix


def dense_decoder(latent_matrix, orig_dims, params):
  """Dense model decoder subgraph that produces output matrix.

  Given encoder latent matrix tensor, the original dimensions of the input, and
  dictionary of parameters, process through dense model decoder subgraph and
  return decoder output matrix.

  Args:
    latent_matrix: tf.float64 matrix tensor of encoder latent matrix.
    orig_dims: Original dimensions of input data.
    params: Dictionary of parameters.

  Returns:
    tf.float64 matrix tensor decoder output vector for each example in batch.
  """
  # Create the input layer to our DNN
  network = latent_matrix

  # Add hidden layers with the given number of units/neurons per layer
  for units in params["dec_dnn_hidden_units"][::-1]:
    network = tf.layers.dense(
        inputs=network,
        units=units,
        activation=tf.nn.relu)

  output_matrix = tf.layers.dense(
      inputs=network,
      units=orig_dims,
      activation=tf.nn.relu)

  return output_matrix


def dense_autoencoder(X, orig_dims, params):
  """Dense model autoencoder using dense encoder and decoder networks.

  Given data matrix tensor X, the original dimensions of the input, and
  dictionary of parameters, process through dense model encoder and decoder
  subgraphs and return reconstructed inputs as output.

  Args:
    X: tf.float64 matrix tensor of input data.
    orig_dims: Original dimensions of input data.
    params: Dictionary of parameters.

  Returns:
    tf.float64 matrix tensor decoder output vector for each example in batch
    that is the reconstructed inputs.
  """
  latent_matrix = dense_encoder(X, params)
  output_matrix = dense_decoder(latent_matrix, orig_dims, params)

  return output_matrix


def dense_autoencoder_model(
    X, mode, params, cur_batch_size, num_feat, dummy_var):
  """Dense autoencoder to reconstruct inputs and minimize reconstruction error.

  Given data matrix tensor X, the current Estimator mode, the dictionary of
  parameters, current batch size, and the number of features, process through
  dense model encoder and decoder subgraphs and return reconstructed inputs
  as output.

  Args:
    X: tf.float64 matrix tensor of input data.
    mode: Estimator ModeKeys. Can take values of TRAIN, EVAL, and PREDICT.
    params: Dictionary of parameters.
    cur_batch_size: Current batch size, could be partially filled.
    num_feat: Number of features.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: Reconstruction loss.
    train_op: Train operation so that Estimator can correctly add to dependency
      graph.
    X_time: 2D tensor representation of time major input data.
    X_time_recon: 3D tensor representation of time major input data.
    X_feat: 2D tensor representation of feature major input data.
    X_feat_recon: 3D tensor representation of feature major input data.
  """
  # Reshape into 2-D tensors
  # Time based
  # shape = (cur_batch_size * seq_len, num_feat)
  X_time = tf.reshape(
      tensor=X,
      shape=[cur_batch_size * params["seq_len"], num_feat])

  # shape = (cur_batch_size * seq_len, num_feat)
  X_time_recon = dense_autoencoder(X_time, num_feat, params)

  # Features based
  # shape = (cur_batch_size, num_feat, seq_len)
  X_transposed = tf.transpose(a=X, perm=[0, 2, 1])
  # shape = (cur_batch_size * num_feat, seq_len)
  X_feat = tf.reshape(
      tensor=X_transposed,
      shape=[cur_batch_size * num_feat, params["seq_len"]])

  # shape = (cur_batch_size * num_feat, seq_len)
  X_feat_recon = dense_autoencoder(X_feat, params["seq_len"], params)

  if (mode == tf.estimator.ModeKeys.TRAIN and
      params["training_mode"] == "reconstruction"):
    X_time_recon_3d = tf.reshape(
        tensor=X_time_recon,
        shape=[cur_batch_size, params["seq_len"], num_feat])
    X_feat_recon_3d = tf.transpose(
        a=tf.reshape(
            tensor=X_feat_recon,
            shape=[cur_batch_size, num_feat, params["seq_len"]]),
        perm=[0, 2, 1])

    X_time_recon_3d_weighted = X_time_recon_3d * params["time_loss_weight"]
    X_feat_recon_3d_weighted = X_feat_recon_3d * params["feat_loss_weight"]

    predictions = (X_time_recon_3d_weighted + X_feat_recon_3d_weighted) \
      / (params["time_loss_weight"] + params["feat_loss_weight"])

    loss = tf.losses.mean_squared_error(labels=X, predictions=predictions)

    train_op = tf.contrib.layers.optimize_loss(
        loss=loss,
        global_step=tf.train.get_global_step(),
        learning_rate=params["learning_rate"],
        optimizer="Adam")

    return loss, train_op, None, None, None, None
  else:
    return None, None, X_time, X_time_recon, X_feat, X_feat_recon


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
    cell:
    infer:
    dnn_hidden_units:
    num_feat:

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
    X, mode, params, cur_batch_size, num_feat, dummy_var):
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
    num_feat: Number of features.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: Reconstruction loss.
    train_op: Train operation so that Estimator can correctly add to dependency
      graph.
    X_time: 2D tensor representation of time major input data.
    X_time_recon: 3D tensor representation of time major input data.
    X_feat: 2D tensor representation of feature major input data.
    X_feat_recon: 3D tensor representation of feature major input data.
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
        num_feat=num_feat)
  else:
    # Since this is inference create fake labels. The list length needs to be
    # the output sequence length even though only the first element is the only
    # one actually used (as our go signal)
    fake_labels = [tf.zeros(shape=[cur_batch_size, num_feat], dtype=tf.float64)
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
        num_feat=num_feat)

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
        units=num_feat,
        activation=None)

  # Now that we are through the final DNN for each sequence element for
  # each example in the batch, reshape the predictions to match our labels.
  # shape = (cur_batch_size, seq_len, num_feat)
  predictions = tf.reshape(
      tensor=logits,
      shape=[cur_batch_size, params["seq_len"], num_feat])

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
        shape=[cur_batch_size * params["seq_len"], num_feat])

    X_time_recon = tf.reshape(
        tensor=predictions,
        shape=[cur_batch_size * params["seq_len"], num_feat])

    # Features based
    # shape = (cur_batch_size, num_feat, seq_len)
    X_transposed = tf.transpose(a=X, perm=[0, 2, 1])

    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat = tf.reshape(
        tensor=X_transposed,
        shape=[cur_batch_size * num_feat, params["seq_len"]])

    # shape = (cur_batch_size, num_feat, seq_len)
    predictions_transposed = tf.transpose(a=predictions, perm=[0, 2, 1])

    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat_recon = tf.reshape(
        tensor=predictions_transposed,
        shape=[cur_batch_size * num_feat, params["seq_len"]])

    return None, None, X_time, X_time_recon, X_feat, X_feat_recon


# PCA model functions
def pca_model(X, mode, params, cur_batch_size, num_feat, dummy_var):
  """PCA to reconstruct inputs and minimize reconstruction error.

  Given data matrix tensor X, the current Estimator mode, the dictionary of
  parameters, current batch size, and the number of features, process through
  PCA model subgraph and return reconstructed inputs as output.

  Args:
    X: tf.float64 matrix tensor of input data.
    mode: Estimator ModeKeys. Can take values of TRAIN, EVAL, and PREDICT.
    params: Dictionary of parameters.
    cur_batch_size: Current batch size, could be partially filled.
    num_feat: Number of features.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: Reconstruction loss.
    train_op: Train operation so that Estimator can correctly add to dependency
      graph.
    X_time: 2D tensor representation of time major input data.
    X_time_recon: 3D tensor representation of time major input data.
    X_feat: 2D tensor representation of feature major input data.
    X_feat_recon: 3D tensor representation of feature major input data.
  """
  # Reshape into 2-D tensors
  # Time based
  # shape = (cur_batch_size * seq_len, num_feat)
  X_time = tf.reshape(
      tensor=X,
      shape=[cur_batch_size * params["seq_len"], num_feat])

  # Features based
  # shape = (cur_batch_size, num_feat, seq_len)
  X_transposed = tf.transpose(a=X, perm=[0, 2, 1])

  # shape = (cur_batch_size * num_feat, seq_len)
  X_feat = tf.reshape(
      tensor=X_transposed,
      shape=[cur_batch_size * num_feat, params["seq_len"]])

  ##############################################################################

  # Variables for calculating error distribution statistics
  with tf.variable_scope(name_or_scope="pca_vars", reuse=tf.AUTO_REUSE):
    # Time based
    pca_time_count_var = tf.get_variable(
        name="pca_time_count_var",
        dtype=tf.int64,
        initializer=tf.zeros(shape=[], dtype=tf.int64),
        trainable=False)

    pca_time_mean_var = tf.get_variable(
        name="pca_time_mean_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[num_feat], dtype=tf.float64),
        trainable=False)

    pca_time_cov_var = tf.get_variable(
        name="pca_time_cov_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[num_feat, num_feat], dtype=tf.float64),
        trainable=False)

    pca_time_eigval_var = tf.get_variable(
        name="pca_time_eigval_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[num_feat], dtype=tf.float64),
        trainable=False)

    pca_time_eigvec_var = tf.get_variable(
        name="pca_time_eigvec_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[num_feat, num_feat], dtype=tf.float64),
        trainable=False)

    # Features based
    pca_feat_count_var = tf.get_variable(
        name="pca_feat_count_var",
        dtype=tf.int64,
        initializer=tf.zeros(shape=[], dtype=tf.int64),
        trainable=False)

    pca_feat_mean_var = tf.get_variable(
        name="pca_feat_mean_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[params["seq_len"]], dtype=tf.float64),
        trainable=False)

    pca_feat_cov_var = tf.get_variable(
        name="pca_feat_cov_var",
        dtype=tf.float64,
        initializer=tf.zeros(
            shape=[params["seq_len"], params["seq_len"]], dtype=tf.float64),
        trainable=False)

    pca_feat_eigval_var = tf.get_variable(
        name="pca_feat_eigval_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[params["seq_len"]], dtype=tf.float64),
        trainable=False)

    pca_feat_eigvec_var = tf.get_variable(
        name="pca_feat_eigvec_var",
        dtype=tf.float64,
        initializer=tf.zeros(
            shape=[params["seq_len"], params["seq_len"]], dtype=tf.float64),
        trainable=False)

  # 3. Loss function, training/eval ops
  if (mode == tf.estimator.ModeKeys.TRAIN and
      params["training_mode"] == "reconstruction"):
    with tf.variable_scope(name_or_scope="pca_vars", reuse=tf.AUTO_REUSE):
      # Check if batch is a singleton or not, very important for covariance math

      # Time based ########################################
      # shape = ()
      singleton_condition = tf.equal(
          x=cur_batch_size * params["seq_len"], y=1)

      pca_time_cov_var, pca_time_mean_var, pca_time_count_var = tf.cond(
          pred=singleton_condition,
          true_fn=lambda: singleton_batch_cov_variable_updating(
              params["seq_len"],
              X_time,
              pca_time_count_var,
              pca_time_mean_var,
              pca_time_cov_var),
          false_fn=lambda: non_singleton_batch_cov_variable_updating(
              cur_batch_size,
              params["seq_len"],
              X_time,
              pca_time_count_var,
              pca_time_mean_var,
              pca_time_cov_var))

      # shape = (num_feat,) & (num_feat, num_feat)
      pca_time_eigval_tensor, pca_time_eigvec_tensor = tf.linalg.eigh(
          tensor=pca_time_cov_var)

      # Features based ########################################
      # shape = ()
      singleton_features_condition = tf.equal(
          x=cur_batch_size * num_feat, y=1)

      pca_feat_cov_var, pca_feat_mean_var, pca_feat_count_var = tf.cond(
          pred=singleton_features_condition,
          true_fn=lambda: singleton_batch_cov_variable_updating(
              num_feat,
              X_feat,
              pca_feat_count_var, pca_feat_mean_var,
              pca_feat_cov_var),
          false_fn=lambda: non_singleton_batch_cov_variable_updating(
              cur_batch_size,
              num_feat,
              X_feat,
              pca_feat_count_var,
              pca_feat_mean_var,
              pca_feat_cov_var))

      # shape = (seq_len,) & (seq_len, seq_len)
      pca_feat_eigval_tensor, pca_feat_eigvec_tensor = tf.linalg.eigh(
          tensor=pca_feat_cov_var)

    # Lastly use control dependencies around loss to enforce the mahalanobis
    # variables to be assigned, the control order matters, hence the separate
    # contexts
    with tf.control_dependencies(
        control_inputs=[pca_time_cov_var, pca_feat_cov_var]):
      with tf.control_dependencies(
          control_inputs=[pca_time_mean_var, pca_feat_mean_var]):
        with tf.control_dependencies(
            control_inputs=[pca_time_count_var, pca_feat_count_var]):
          with tf.control_dependencies(
              control_inputs=[tf.assign(ref=pca_time_eigval_var,
                                        value=pca_time_eigval_tensor),
                              tf.assign(ref=pca_time_eigvec_var,
                                        value=pca_time_eigvec_tensor),
                              tf.assign(ref=pca_feat_eigval_var,
                                        value=pca_feat_eigval_tensor),
                              tf.assign(ref=pca_feat_eigvec_var,
                                        value=pca_feat_eigvec_tensor)]):
            loss = tf.reduce_sum(
                input_tensor=tf.zeros(
                    shape=(), dtype=tf.float64) * dummy_var)

            train_op = tf.contrib.layers.optimize_loss(
                loss=loss,
                global_step=tf.train.get_global_step(),
                learning_rate=params["learning_rate"],
                optimizer="SGD")

            return loss, train_op, None, None, None, None
  else:
    # Time based
    # shape = (cur_batch_size * seq_len, num_feat)
    X_time = X_time - pca_time_mean_var

    # shape = (cur_batch_size * seq_len, params["k_principal_components"])
    X_time_projected = tf.matmul(
        a=X_time,
        b=pca_time_eigvec_var[:, -params["k_principal_components"]:])

    # shape = (cur_batch_size * seq_len, num_feat)
    X_time_recon = tf.matmul(
        a=X_time_projected,
        b=pca_time_eigvec_var[:, -params["k_principal_components"]:],
        transpose_b=True)

    # Features based
    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat = X_feat - pca_feat_mean_var

    # shape = (cur_batch_size * num_feat, params["k_principal_components"])
    X_feat_projected = tf.matmul(
        a=X_feat,
        b=pca_feat_eigvec_var[:, -params["k_principal_components"]:])

    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat_recon = tf.matmul(
        a=X_feat_projected,
        b=pca_feat_eigvec_var[:, -params["k_principal_components"]:],
        transpose_b=True)

    return None, None, X_time, X_time_recon, X_feat, X_feat_recon


# Anomaly detection model functions
def create_mahalanobis_dist_vars(var_name, size):
  """Creates mahalanobis distance variables.

  Given variable name and size, create and return mahalanobis distance variables
  for count, mean, covariance, and inverse covariance.

  Args:
    var_name: String denoting which set of variables to create. Values are
      "time" and "feat".
    size: The size of the variable, either sequence length or number of
      features.

  Returns:
    Mahalanobis distance variables for count, mean, covariance, and inverse
    covariance.
  """
  with tf.variable_scope(
      name_or_scope="mahalanobis_dist_vars", reuse=tf.AUTO_REUSE):
    count_var = tf.get_variable(
        name="abs_err_count_{0}_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.zeros(shape=[], dtype=tf.int64),
        trainable=False)

    mean_var = tf.get_variable(
        name="abs_err_mean_{0}_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(shape=[size], dtype=tf.float64),
        trainable=False)

    cov_var = tf.get_variable(
        name="abs_err_cov_{0}_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(shape=[size, size], dtype=tf.float64),
        trainable=False)

    inv_cov_var = tf.get_variable(
        name="abs_err_inv_cov_{0}_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(shape=[size, size], dtype=tf.float64),
        trainable=False)

  return count_var, mean_var, cov_var, inv_cov_var


def create_both_mahalanobis_dist_vars(seq_len, num_feat):
  """Creates both time & feature major mahalanobis distance variables.

  Given dimensions of inputs, create and return mahalanobis distance variables
  for count, mean, covariance, and inverse covariance for both time and
  feature major representations.

  Args:
    seq_len: Number of timesteps in sequence.
    num_feat: Number of features.

  Returns:
    Mahalanobis distance variables for count, mean, covariance, and inverse
    covariance for both time and feature major representations.
  """
  # Time based
  (abs_err_count_time_var,
   abs_err_mean_time_var,
   abs_err_cov_time_var,
   abs_err_inv_cov_time_var) = create_mahalanobis_dist_vars(
       var_name="time", size=num_feat)

  # Features based
  (abs_err_count_feat_var,
   abs_err_mean_feat_var,
   abs_err_cov_feat_var,
   abs_err_inv_cov_feat_var) = create_mahalanobis_dist_vars(
       var_name="feat", size=seq_len)

  return (abs_err_count_time_var,
          abs_err_mean_time_var,
          abs_err_cov_time_var,
          abs_err_inv_cov_time_var,
          abs_err_count_feat_var,
          abs_err_mean_feat_var,
          abs_err_cov_feat_var,
          abs_err_inv_cov_feat_var)


def create_confusion_matrix_thresh_vars(scope, var_name, size):
  """Creates confusion matrix threshold variables.

  Given variable scope, name, and size, create and return confusion matrix
  threshold variables for true positives, false negatives, false positives,
  true negatives.

  Args:
    scope: String of variable scope name.
    var_name: String denoting which set of variables to create. Values are
      "time" and "feat".
    size: The size of the variable, number of time/feature thresholds.

  Returns:
    Confusion matrix threshold variables for true positives, false negatives,
    false positives, true negatives.
  """
  with tf.variable_scope(
      name_or_scope=scope, reuse=tf.AUTO_REUSE):
    tp_thresh_var = tf.get_variable(
        name="tp_thresh_{0}_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.zeros(
            shape=size, dtype=tf.int64),
        trainable=False)

    fn_thresh_var = tf.get_variable(
        name="fn_thresh_{0}_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.zeros(
            shape=size, dtype=tf.int64),
        trainable=False)

    fp_thresh_var = tf.get_variable(
        name="fp_thresh_{0}_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.zeros(
            shape=size, dtype=tf.int64),
        trainable=False)

    tn_thresh_var = tf.get_variable(
        name="tn_thresh_{0}_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.zeros(
            shape=size, dtype=tf.int64),
        trainable=False)

    return (tp_thresh_var,
            fn_thresh_var,
            fp_thresh_var,
            tn_thresh_var)


def create_both_confusion_matrix_thresh_vars(
    scope, time_thresh_size, feat_thresh_size):
  """Creates both time & feature major confusion matrix threshold variables.

  Given variable scope and sizes, create and return confusion
  matrix threshold variables for true positives, false negatives, false
  positives, and true negatives for both time and feature major
  representations.

  Args:
    scope: String of variable scope name.
    time_thresh_size: Variable size of number of time major thresholds.
    feat_thresh_size: Variable size of number of feature major thresholds.

  Returns:
    Confusion matrix threshold variables for true positives, false negatives,
    false positives, true negatives for both time and feature major
    representations.
  """
  # Time based
  (tp_thresh_time_var,
   fn_thresh_time_var,
   fp_thresh_time_var,
   tn_thresh_time_var) = create_confusion_matrix_thresh_vars(
       scope=scope, var_name="time", size=time_thresh_size)

  # Features based
  (tp_thresh_feat_var,
   fn_thresh_feat_var,
   fp_thresh_feat_var,
   tn_thresh_feat_var) = create_confusion_matrix_thresh_vars(
       scope=scope, var_name="feat", size=feat_thresh_size)

  return (tp_thresh_time_var,
          fn_thresh_time_var,
          fp_thresh_time_var,
          tn_thresh_time_var,
          tp_thresh_feat_var,
          fn_thresh_feat_var,
          fp_thresh_feat_var,
          tn_thresh_feat_var)

def create_mahalanobis_unsupervised_thresh_vars(scope, var_name):
  """Creates mahalanobis unsupervised threshold variables.

  Given variable scope and name, create and return mahalanobis unsupervised
  threshold variables of mean and standard deviation.

  Args:
    scope: String of variable scope name.
    var_name: String denoting which set of variables to create. Values are
      "time" and "feat".

  Returns:
    Mahalanobis unsupervised threshold variables of count, mean, and standard
    deviation.
  """
  with tf.variable_scope(
      name_or_scope=scope, reuse=tf.AUTO_REUSE):
    count_thresh_var = tf.get_variable(
        name="count_thresh_{0}_var".format(var_name),
        dtype=tf.int64,
        initializer=tf.zeros(
            shape=[], dtype=tf.int64),
        trainable=False)

    mean_thresh_var = tf.get_variable(
        name="mean_thresh_{0}_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(
            shape=[], dtype=tf.float64),
        trainable=False)

    var_thresh_var = tf.get_variable(
        name="var_thresh_{0}_var".format(var_name),
        dtype=tf.float64,
        initializer=tf.zeros(
            shape=[], dtype=tf.float64),
        trainable=False)

    return (count_thresh_var,
            mean_thresh_var,
            var_thresh_var)


def create_both_mahalanobis_unsupervised_thresh_vars(scope):
  """Creates time & feature mahalanobis unsupervised threshold variables.

  Given variable scope, create and return mahalanobis unsupervised
  threshold variables of mean and standard deviation for both time and
  feature major representations.

  Args:
    scope: String of variable scope name.

  Returns:
    Mahalanobis unsupervised threshold variables of mean and standard
    deviation for both time and feature major representations.
  """
  # Time based
  (count_thresh_time_var,
   mean_thresh_time_var,
   var_thresh_time_var) = create_mahalanobis_unsupervised_thresh_vars(
       scope=scope, var_name="time")

  # Features based
  (count_thresh_feat_var,
   mean_thresh_feat_var,
   var_thresh_feat_var) = create_mahalanobis_unsupervised_thresh_vars(
       scope=scope, var_name="feat")

  return (count_thresh_time_var,
          mean_thresh_time_var,
          var_thresh_time_var,
          count_thresh_feat_var,
          mean_thresh_feat_var,
          var_thresh_feat_var)


# Running covariance updating functions for mahalanobis distance variables
def update_record_count(count_a, count_b):
  """Updates the running number of records processed.

  Given previous running total and current batch size, return new running total.

  Args:
    count_a: tf.int64 scalar tensor of previous running total of records.
    count_b: tf.int64 scalar tensor of current batch size.

  Returns:
    A tf.int64 scalar tensor of new running total of records.
  """
  return count_a + count_b


# Incremental covariance updating functions for mahalanobis distance variables


def update_mean_incremental(count_a, mean_a, value_b):
  """Updates the running mean vector incrementally.

  Given previous running total, running column means, and single example's
  column values, return new running column means.

  Args:
    count_a: tf.int64 scalar tensor of previous running total of records.
    mean_a: tf.float64 vector tensor of previous running column means.
    value_b: tf.float64 vector tensor of single example's column values.

  Returns:
    A tf.float64 vector tensor of new running column means.
  """
  umean_a = mean_a * tf.cast(x=count_a, dtype=tf.float64)
  mean_ab_num = umean_a + tf.squeeze(input=value_b, axis=0)
  mean_ab = mean_ab_num / tf.cast(x=count_a + 1, dtype=tf.float64)

  return mean_ab


# This function updates the covariance matrix incrementally
def update_cov_incremental(
    count_a, mean_a, cov_a, value_b, mean_ab, sample_cov):
  """Updates the running covariance matrix incrementally.

  Given previous running total, running column means, running covariance matrix,
  single example's column values, new running column means, and whether to use
  sample covariance or not, return new running covariance matrix.

  Args:
    count_a: tf.int64 scalar tensor of previous running total of records.
    mean_a: tf.float64 vector tensor of previous running column means.
    cov_a: tf.float64 matrix tensor of previous running covariance matrix.
    value_b: tf.float64 vector tensor of single example's column values.
    mean_ab: tf.float64 vector tensor of new running column means.
    sample_cov: Bool flag on whether sample or population covariance is used.

  Returns:
    A tf.float64 matrix tensor of new covariance matrix.
  """
  print("value_b = \n{}".format(value_b))
  print("mean_a = \n{}".format(mean_a))
  print("mean_ab = \n{}".format(mean_ab))
  mean_diff = tf.matmul(
      a=value_b - mean_a, b=value_b - mean_ab, transpose_a=True)
  if sample_cov:
    ucov_a = cov_a * tf.cast(x=count_a - 1, dtype=tf.float64)
    cov_ab = (ucov_a + mean_diff) / tf.cast(x=count_a, dtype=tf.float64)
  else:
    ucov_a = cov_a * tf.cast(x=count_a, dtype=tf.float64)
    cov_ab = (ucov_a + mean_diff) / tf.cast(x=count_a + 1, dtype=tf.float64)

  return cov_ab


def singleton_batch_cov_variable_updating(
    inner_size, X, count_variable, mean_variable, cov_variable):
  """Updates mahalanobis variables incrementally when number_of_rows equals 1.

  Given the inner size of the matrix, the data vector X, the variable tracking
  running record counts, the variable tracking running column means, and the
  variable tracking running covariance matrix, returns updated running
  covariance matrix, running column means, and running record count variables.

  Args:
    inner_size: Inner size of matrix X.
    X: tf.float64 matrix tensor of input data.
    count_variable: tf.int64 scalar variable tracking running record counts.
    mean_variable: tf.float64 vector variable tracking running column means.
    cov_variable: tf.float64 matrix variable tracking running covariance matrix.

  Returns:
    Updated running covariance matrix, running column means, and running record
      count variables.
  """
  # Calculate new combined mean for incremental covariance matrix calculation
  # time_shape = (num_feat,), features_shape = (seq_len,)
  mean_ab = update_mean_incremental(
      count_a=count_variable, mean_a=mean_variable, value_b=X)

  # Update running variables from single example
  # time_shape = (), features_shape = ()
  count_tensor = update_record_count(count_a=count_variable, count_b=1)

  # time_shape = (num_feat,), features_shape = (seq_len,)
  mean_tensor = mean_ab

  # Check if inner dimension is greater than 1 to calculate covariance matrix
  if inner_size == 1:
    cov_tensor = tf.zeros_like(tensor=cov_variable, dtype=tf.float64)
  else:
    # time_shape = (num_feat, num_feat)
    # features_shape = (seq_len, seq_len)
    cov_tensor = update_cov_incremental(
        count_a=count_variable,
        mean_a=mean_variable,
        cov_a=cov_variable,
        value_b=X,
        mean_ab=mean_ab,
        sample_cov=True)

  # Assign values to variables, use control dependencies around return to
  # enforce the mahalanobis variables to be assigned, the control order matters,
  # hence the separate contexts.
  with tf.control_dependencies(
      control_inputs=[tf.assign(ref=cov_variable, value=cov_tensor)]):
    with tf.control_dependencies(
        control_inputs=[tf.assign(ref=mean_variable, value=mean_tensor)]):
      with tf.control_dependencies(
          control_inputs=[tf.assign(ref=count_variable, value=count_tensor)]):

        return (tf.identity(input=cov_variable),
                tf.identity(input=mean_variable),
                tf.identity(input=count_variable))


def singleton_batch_var_variable_updating(
    inner_size, x, count_variable, mean_variable, var_variable):
  """Updates mahalanobis thresh vars incrementally when number_of_rows equals 1.

  Given the inner size of the matrix, the data scalar x, the variable tracking
  running record counts, the variable tracking the running mean, and the
  variable tracking the running variance, returns updated running variance,
  running mean, and running record count variables.

  Args:
    inner_size: Inner size of matrix X.
    x: tf.float64 scalar tensor of input data.
    count_variable: tf.int64 scalar variable tracking running record counts.
    mean_variable: tf.float64 scalar variable tracking running mean.
    var_variable: tf.float64 scalar variable tracking running variance.

  Returns:
    Updated running variance, running mean, and running record count variables.
  """
  # Calculate new combined mean for incremental covariance matrix calculation
  # time_shape = (), features_shape = ()
  mean_ab = update_mean_incremental(
      count_a=count_variable, mean_a=mean_variable, value_b=x)

  # Update running variables from single example
  # time_shape = (), features_shape = ()
  count_tensor = update_record_count(count_a=count_variable, count_b=1)

  # time_shape = (), features_shape = ()
  mean_tensor = mean_ab

  # Check if inner dimension is greater than 1 to calculate covariance matrix
  if inner_size == 1:
    var_tensor = tf.zeros_like(tensor=var_variable, dtype=tf.float64)
  else:
    # time_shape = (), features_shape = ()
    var_tensor = update_cov_incremental(
        count_a=count_variable,
        mean_a=tf.reshape(tensor=mean_variable, shape=[1]),
        cov_a=tf.reshape(tensor=var_variable, shape=[1, 1]),
        value_b=tf.reshape(tensor=x, shape=[1,1]),
        mean_ab=tf.reshape(tensor=mean_ab, shape=[1]),
        sample_cov=True)

    var_tensor = tf.squeeze(input=var_tensor)

  # Assign values to variables, use control dependencies around return to
  # enforce the mahalanobis variables to be assigned, the control order matters,
  # hence the separate contexts.
  with tf.control_dependencies(
      control_inputs=[tf.assign(ref=var_variable, value=var_tensor)]):
    with tf.control_dependencies(
        control_inputs=[tf.assign(ref=mean_variable, value=mean_tensor)]):
      with tf.control_dependencies(
          control_inputs=[tf.assign(ref=count_variable, value=count_tensor)]):

        return (tf.identity(input=var_variable),
                tf.identity(input=mean_variable),
                tf.identity(input=count_variable))


# Batch covariance updating functions for mahalanobis distance variables


def update_mean_batch(count_a, mean_a, count_b, mean_b):
  """Updates the running mean vector with a batch of data.

  Given previous running total, running column means, current batch size, and
  batch's column means, return new running column means.

  Args:
    count_a: tf.int64 scalar tensor of previous running total of records.
    mean_a: tf.float64 vector tensor of previous running column means.
    count_b: tf.int64 scalar tensor of current batch size.
    mean_b: tf.float64 vector tensor of batch's column means.

  Returns:
    A tf.float64 vector tensor of new running column means.
  """
  sum_a = mean_a * tf.cast(x=count_a, dtype=tf.float64)
  sum_b = mean_b * tf.cast(x=count_b, dtype=tf.float64)
  mean_ab = (sum_a + sum_b) / tf.cast(x=count_a + count_b, dtype=tf.float64)

  return mean_ab


def update_cov_batch(
    count_a, mean_a, cov_a, count_b, mean_b, cov_b, sample_cov):
  """Updates the running covariance matrix with batch of data.

  Given previous running total, running column means, running covariance matrix,
  current batch size, batch's column means, batch's covariance matrix, and
  whether to use sample covariance or not, return new running covariance matrix.

  Args:
    count_a: tf.int64 scalar tensor of previous running total of records.
    mean_a: tf.float64 vector tensor of previous running column means.
    cov_a: tf.float64 matrix tensor of previous running covariance matrix.
    count_b: tf.int64 scalar tensor of current batch size.
    mean_b: tf.float64 vector tensor of batch's column means.
    cov_b: tf.float64 matrix tensor of batch's covariance matrix.
    sample_cov: Bool flag on whether sample or population covariance is used.

  Returns:
    A tf.float64 matrix tensor of new running covariance matrix.
  """
  mean_diff = tf.expand_dims(input=mean_a - mean_b, axis=0)

  if sample_cov:
    ucov_a = cov_a * tf.cast(x=count_a - 1, dtype=tf.float64)
    ucov_b = cov_b * tf.cast(x=count_b - 1, dtype=tf.float64)
    den = tf.cast(x=count_a + count_b - 1, dtype=tf.float64)
  else:
    ucov_a = cov_a * tf.cast(x=count_a, dtype=tf.float64)
    ucov_b = cov_b * tf.cast(x=count_b, dtype=tf.float64)
    den = tf.cast(x=count_a + count_b, dtype=tf.float64)

  mean_diff = tf.matmul(a=mean_diff, b=mean_diff, transpose_a=True)
  mean_scaling_num = tf.cast(x=count_a * count_b, dtype=tf.float64)
  mean_scaling_den = tf.cast(x=count_a + count_b, dtype=tf.float64)
  mean_scaling = mean_scaling_num / mean_scaling_den
  cov_ab = (ucov_a + ucov_b + mean_diff * mean_scaling) / den

  return cov_ab


def non_singleton_batch_cov_variable_updating(
    cur_batch_size, inner_size, X, count_variable, mean_variable, cov_variable):
  """Updates mahalanobis variables when number_of_rows does NOT equal 1.

  Given the current batch size, inner size of the matrix, the data matrix X,
  the variable tracking running record counts, the variable tracking running
  column means, and the variable tracking running covariance matrix, returns
  updated running covariance matrix, running column means, and running record
  count variables.

  Args:
    cur_batch_size: Number of examples in current batch (could be partial).
    inner_size: Inner size of matrix X.
    X: tf.float64 matrix tensor of input data.
    count_variable: tf.int64 scalar variable tracking running record counts.
    mean_variable: tf.float64 vector variable tracking running column means.
    cov_variable: tf.float64 matrix variable tracking running covariance matrix.

  Returns:
    Updated running covariance matrix, running column means, and running record
      count variables.
  """
  # Find statistics of batch
  number_of_rows = cur_batch_size * inner_size

  # time_shape = (num_feat,), features_shape = (seq_len,)
  X_mean = tf.reduce_mean(input_tensor=X, axis=0)

  # time_shape = (cur_batch_size * seq_len, num_feat)
  # features_shape = (cur_batch_size * num_feat, seq_len)
  X_centered = X - X_mean

  if inner_size > 1:
    # time_shape = (num_feat, num_feat)
    # features_shape = (seq_len, seq_len)
    X_cov = tf.matmul(
        a=X_centered,
        b=X_centered,
        transpose_a=True) / tf.cast(x=number_of_rows - 1, dtype=tf.float64)

  # Update running variables from batch statistics
  # time_shape = (), features_shape = ()
  count_tensor = update_record_count(
      count_a=count_variable, count_b=number_of_rows)

  # time_shape = (num_feat,), features_shape = (seq_len,)
  mean_tensor = update_mean_batch(
      count_a=count_variable,
      mean_a=mean_variable,
      count_b=number_of_rows,
      mean_b=X_mean)

  # Check if inner dimension is greater than 1 to calculate covariance matrix
  if inner_size == 1:
    cov_tensor = tf.zeros_like(tensor=cov_variable, dtype=tf.float64)
  else:
    # time_shape = (num_feat, num_feat)
    # features_shape = (seq_len, seq_len)
    cov_tensor = update_cov_batch(
        count_a=count_variable,
        mean_a=mean_variable,
        cov_a=cov_variable,
        count_b=number_of_rows,
        mean_b=X_mean,
        cov_b=X_cov,
        sample_cov=True)

  # Assign values to variables, use control dependencies around return to
  # enforce the mahalanobis variables to be assigned, the control order matters,
  # hence the separate contexts.
  with tf.control_dependencies(
      control_inputs=[tf.assign(ref=cov_variable, value=cov_tensor)]):
    with tf.control_dependencies(
        control_inputs=[tf.assign(ref=mean_variable, value=mean_tensor)]):
      with tf.control_dependencies(
          control_inputs=[tf.assign(ref=count_variable, value=count_tensor)]):

        return (tf.identity(input=cov_variable),
                tf.identity(input=mean_variable),
                tf.identity(input=count_variable))


def non_singleton_batch_var_variable_updating(
    cur_batch_size, inner_size, x, count_variable, mean_variable, var_variable):
  """Updates mahalanobis thresh variables when number_of_rows does NOT equal 1.

  Given the current batch size, inner size of the matrix, the data vector x,
  the variable tracking the running record count, the variable tracking the
  running mean, and the variable tracking the running variance, returns
  updated running variance, running mean, and running record count variables.

  Args:
    cur_batch_size: Number of examples in current batch (could be partial).
    inner_size: Inner size of matrix X.
    x: tf.float64 vector tensor of mahalanobis distance.
    count_variable: tf.int64 scalar variable tracking running record count.
    mean_variable: tf.float64 scalar variable tracking running mean.
    var_variable: tf.float64 scalar variable tracking running variance.

  Returns:
    Updated running variance, running mean, and running record count variables.
  """
  # Find statistics of batch
  number_of_rows = cur_batch_size * inner_size
  
  # time_shape = (), features_shape = ()
  x_mean = tf.reduce_mean(input_tensor=x)

  # time_shape = (cur_batch_size * seq_len,)
  # features_shape = (cur_batch_size * num_feat,)
  x_centered = x - x_mean

  if inner_size > 1:
    # time_shape = (), features_shape = ()
    x_var = tf.reduce_sum(input_tensor=tf.square(x=x_centered))
    x_var /= tf.cast(x=number_of_rows - 1, dtype=tf.float64)

  # Update running variables from batch statistics
  # time_shape = (), features_shape = ()
  count_tensor = update_record_count(
      count_a=count_variable, count_b=number_of_rows)

  # time_shape = (), features_shape = ()
  mean_tensor = update_mean_batch(
      count_a=count_variable,
      mean_a=mean_variable,
      count_b=number_of_rows,
      mean_b=x_mean)

  # Check if inner dimension is greater than 1 to calculate covariance matrix
  if inner_size == 1:
    var_tensor = tf.zeros_like(tensor=var_variable, dtype=tf.float64)
  else:
    # time_shape = (num_feat, num_feat)
    # features_shape = (seq_len, seq_len)
    var_tensor = update_cov_batch(
        count_a=count_variable,
        mean_a=mean_variable,
        cov_a=var_variable,
        count_b=number_of_rows,
        mean_b=tf.expand_dims(input=x_mean, axis=0),
        cov_b=tf.reshape(tensor=x_var, shape=[1, 1]),
        sample_cov=True)

    var_tensor = tf.squeeze(input=var_tensor)

  # Assign values to variables, use control dependencies around return to
  # enforce the mahalanobis thresh variables to be assigned, the control order
  # matters, hence the separate contexts.
  with tf.control_dependencies(
      control_inputs=[tf.assign(ref=var_variable, value=var_tensor)]):
    with tf.control_dependencies(
        control_inputs=[tf.assign(ref=mean_variable, value=mean_tensor)]):
      with tf.control_dependencies(
          control_inputs=[tf.assign(ref=count_variable, value=count_tensor)]):

        return (tf.identity(input=var_variable),
                tf.identity(input=mean_variable),
                tf.identity(input=count_variable))


def mahalanobis_dist(err_vec, mean_vec, inv_cov, final_shape):
  """Calculates mahalanobis distance from MLE.

  Given reconstruction error vector, mean reconstruction error vector, inverse
  covariance of reconstruction error, and mahalanobis distance tensor's final
  shape, return mahalanobis distance.

  Args:
    err_vec: tf.float64 matrix tensor of reconstruction errors.
    mean_vec: tf.float64 vector variable tracking running column means of
      reconstruction errors.
    inv_cov: tf.float64 matrix variable tracking running covariance matrix of
      reconstruction errors.
    final_shape: Final shape of mahalanobis distance tensor.

  Returns:
    tf.float64 matrix tensor of mahalanobis distance.
  """
  # time_shape = (cur_batch_size * seq_len, num_feat)
  # features_shape = (cur_batch_size * num_feat, seq_len)
  err_vec_cen = err_vec - mean_vec

  # time_shape = (num_feat, cur_batch_size * seq_len)
  # features_shape = (seq_len, cur_batch_size * num_feat)
  mahalanobis_right_product = tf.matmul(
      a=inv_cov, b=err_vec_cen, transpose_b=True)

  # time_shape = (cur_batch_size * seq_len, cur_batch_size * seq_len)
  # features_shape = (cur_batch_size * num_feat, cur_batch_size * num_feat)
  mahalanobis_dist_vectorized = tf.matmul(
      a=err_vec_cen, b=mahalanobis_right_product)

  # time_shape = (cur_batch_size * seq_len,)
  # features_shape = (cur_batch_size * num_feat,)
  mahalanobis_dist_flat = tf.diag_part(input=mahalanobis_dist_vectorized)

  # time_shape = (cur_batch_size, seq_len)
  # features_shape = (cur_batch_size, num_feat)
  mahalanobis_dist_final_shaped = tf.reshape(
      tensor=mahalanobis_dist_flat, shape=[-1, final_shape])

  # time_shape = (cur_batch_size, seq_len)
  # features_shape = (cur_batch_size, num_feat)
  mahalanobis_dist_final_shaped_sqrt = tf.sqrt(x=mahalanobis_dist_final_shaped)

  return mahalanobis_dist_final_shaped_sqrt


def calculate_error_distribution_statistics_training(
    cur_batch_size,
    num_feat,
    X_time_abs_recon_err,
    abs_err_count_time_var,
    abs_err_mean_time_var,
    abs_err_cov_time_var,
    abs_err_inv_cov_time_var,
    X_feat_abs_recon_err,
    abs_err_count_feat_var,
    abs_err_mean_feat_var,
    abs_err_cov_feat_var,
    abs_err_inv_cov_feat_var,
    params,
    dummy_var):
  """Calculates error distribution statistics during training mode.

  Given dimensions of inputs, reconstructed inputs' absolute errors, and
  variables tracking counts, means, and covariances of error distribution,
  returns loss and train_op.

  Args:
    cur_batch_size: Current batch size, could be partially filled.
    num_feat: Number of features.
    X_time_abs_recon_err: Time major reconstructed input data's absolute
      reconstruction error.
    abs_err_count_time_var: Time major running count of number of records.
    abs_err_mean_time_var: Time major running column means of absolute error.
    abs_err_cov_time_var: Time major running covariance matrix of absolute
      error.
    abs_err_inv_cov_time_var: Time major running inverse covariance matrix of
    absolute error.
    X_feat_abs_recon_err: Feature major reconstructed input data's absolute
      reconstruction error.
    abs_err_count_feat_var: Feature major running count of number of records.
    abs_err_mean_feat_var: Feature major running column means of absolute error.
    abs_err_cov_feat_var: Feature major running covariance matrix of absolute
      error.
    abs_err_inv_cov_feat_var: Feature major running inverse covariance matrix of
    absolute error.
    params: Dictionary of parameters.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: The scalar loss to tie our updates back to Estimator graph.
    train_op: The train operation to tie our updates back to Estimator graph.
  """
  with tf.variable_scope(
      name_or_scope="mahalanobis_dist_vars", reuse=tf.AUTO_REUSE):
    # Time based
    singleton_time_condition = tf.equal(
        x=cur_batch_size * params["seq_len"], y=1)

    cov_time_var, mean_time_var, count_time_var = tf.cond(
        pred=singleton_time_condition,
        true_fn=lambda: singleton_batch_cov_variable_updating(
            params["seq_len"],
            X_time_abs_recon_err,
            abs_err_count_time_var,
            abs_err_mean_time_var,
            abs_err_cov_time_var),
        false_fn=lambda: non_singleton_batch_cov_variable_updating(
            cur_batch_size,
            params["seq_len"],
            X_time_abs_recon_err,
            abs_err_count_time_var,
            abs_err_mean_time_var,
            abs_err_cov_time_var))

    # Features based
    singleton_feat_condition = tf.equal(
        x=cur_batch_size * num_feat, y=1)

    cov_feat_var, mean_feat_var, count_feat_var = tf.cond(
        pred=singleton_feat_condition,
        true_fn=lambda: singleton_batch_cov_variable_updating(
            num_feat,
            X_feat_abs_recon_err,
            abs_err_count_feat_var,
            abs_err_mean_feat_var,
            abs_err_cov_feat_var),
        false_fn=lambda: non_singleton_batch_cov_variable_updating(
            cur_batch_size,
            num_feat,
            X_feat_abs_recon_err,
            abs_err_count_feat_var,
            abs_err_mean_feat_var,
            abs_err_cov_feat_var))

  # Lastly use control dependencies around loss to enforce the mahalanobis
  # variables to be assigned, the control order matters, hence the separate
  # contexts
  with tf.control_dependencies(
      control_inputs=[cov_time_var, cov_feat_var]):
    with tf.control_dependencies(
        control_inputs=[mean_time_var, mean_feat_var]):
      with tf.control_dependencies(
          control_inputs=[count_time_var, count_feat_var]):
        # Time based
        # shape = (num_feat, num_feat)
        abs_err_inv_cov_time_tensor = \
          tf.matrix_inverse(input=cov_time_var + \
            tf.eye(num_rows=tf.shape(input=cov_time_var)[0],
                   dtype=tf.float64) * params["eps"])
        # Features based
        # shape = (seq_len, seq_len)
        abs_err_inv_cov_feat_tensor = \
          tf.matrix_inverse(input=cov_feat_var + \
            tf.eye(num_rows=tf.shape(input=cov_feat_var)[0],
                   dtype=tf.float64) * params["eps"])

        with tf.control_dependencies(
            control_inputs=[tf.assign(ref=abs_err_inv_cov_time_var,
                                      value=abs_err_inv_cov_time_tensor),
                            tf.assign(ref=abs_err_inv_cov_feat_var,
                                      value=abs_err_inv_cov_feat_tensor)]):
          loss = tf.reduce_sum(
              input_tensor=tf.zeros(shape=(), dtype=tf.float64) * dummy_var)

          train_op = tf.contrib.layers.optimize_loss(
              loss=loss,
              global_step=tf.train.get_global_step(),
              learning_rate=params["learning_rate"],
              optimizer="SGD")

  return loss, train_op


def reconstruction_evaluation(X_time_orig, X_time_recon, training_mode):
  """Reconstruction loss on evaluation set.

  Given time major original and reconstructed features data and the training
  mode, return loss and eval_metrics_ops.

  Args:
    X_time_orig: Time major original features data.
    X_time_recon: Time major reconstructed features data.
    training_mode: Current training mode.

  Returns:
    loss: Scalar reconstruction loss.
    eval_metric_ops: Evaluation metrics of reconstruction.
  """
  loss = tf.losses.mean_squared_error(
      labels=X_time_orig, predictions=X_time_recon)

  eval_metric_ops = None

  if training_mode == "reconstruction":
    # Reconstruction eval metrics
    eval_metric_ops = {
        "rmse": tf.metrics.root_mean_squared_error(
            labels=X_time_orig, predictions=X_time_recon),
        "mae": tf.metrics.mean_absolute_error(
            labels=X_time_orig, predictions=X_time_recon)
    }

  return loss, eval_metric_ops


def update_anom_thresh_vars(
    labels_norm_mask,
    labels_anom_mask,
    num_thresh,
    anom_thresh,
    mahalanobis_dist,
    tp_at_thresh_var,
    fn_at_thresh_var,
    fp_at_thresh_var,
    tn_at_thresh_var,
    mode):
  """Updates anomaly threshold variables.

  Given masks for when labels are normal and anomalous, the number of anomaly
  thresholds and the thresholds themselves, the mahalanobis distance, variables
  for the confusion matrix, and the current Estimator mode, returns the updated
  variables for the confusion matrix.

  Args:
    labels_norm_mask: tf.bool vector tensor that is true when label was normal.
    labels_anom_mask: tf.bool vector tensor that is true when label was
      anomalous.
    num_thresh: Number of anomaly thresholds to try in parallel grid search.
    anom_thresh: tf.float64 vector tensor of grid of anomaly thresholds to try.
    mahalanobis_dist: tf.float64 matrix tensor of mahalanobis distances across
      batch.
    tp_at_thresh_var: tf.int64 variable tracking number of true positives at
      each possible anomaly threshold.
    fn_at_thresh_var: tf.int64 variable tracking number of false negatives at
      each possible anomaly threshold.
    fp_at_thresh_var: tf.int64 variable tracking number of false positives at
      each possible anomaly threshold.
    tn_at_thresh_var: tf.int64 variable tracking number of true negatives at
      each possible anomaly threshold.
    mode: Estimator ModeKeys, can take values of TRAIN and EVAL.

  Returns:
    Updated confusion matrix variables.
  """
  if mode == tf.estimator.ModeKeys.TRAIN:
    # time_shape = (num_time_anom_thresh, cur_batch_size, seq_len)
    # feat_shape = (num_feat_anom_thresh, cur_batch_size, num_feat)
    mahalanobis_dist_over_thresh = tf.map_fn(
        fn=lambda anom_threshold: mahalanobis_dist > anom_threshold,
        elems=anom_thresh,
        dtype=tf.bool)
  else:
    # time_shape = (cur_batch_size, seq_len)
    # feat_shape = (cur_batch_size, num_feat)
    mahalanobis_dist_over_thresh = mahalanobis_dist > anom_thresh

  # time_shape = (num_time_anom_thresh, cur_batch_size)
  # feat_shape = (num_feat_anom_thresh, cur_batch_size)
  mahalanobis_dist_any_over_thresh = tf.reduce_any(
      input_tensor=mahalanobis_dist_over_thresh, axis=-1)

  if mode == tf.estimator.ModeKeys.EVAL:
    # time_shape = (1, cur_batch_size)
    # feat_shape = (1, cur_batch_size)
    mahalanobis_dist_any_over_thresh = tf.expand_dims(
        input=mahalanobis_dist_any_over_thresh, axis=0)

  # time_shape = (num_time_anom_thresh, cur_batch_size)
  # feat_shape = (num_feat_anom_thresh, cur_batch_size)
  predicted_normals = tf.equal(
      x=mahalanobis_dist_any_over_thresh, y=False)

  # time_shape = (num_time_anom_thresh, cur_batch_size)
  # feat_shape = (num_feat_anom_thresh, cur_batch_size)
  predicted_anomalies = tf.equal(
      x=mahalanobis_dist_any_over_thresh, y=True)

  # Calculate confusion matrix of current batch
  # time_shape = (num_time_anom_thresh,)
  # feat_shape = (num_feat_anom_thresh,)
  tp = tf.reduce_sum(
      input_tensor=tf.cast(
          x=tf.map_fn(
              fn=lambda threshold: tf.logical_and(
                  x=labels_anom_mask,
                  y=predicted_anomalies[threshold, :]),
              elems=tf.range(start=0, limit=num_thresh, dtype=tf.int64),
              dtype=tf.bool),
          dtype=tf.int64),
      axis=1)

  fn = tf.reduce_sum(
      input_tensor=tf.cast(
          x=tf.map_fn(
              fn=lambda threshold: tf.logical_and(
                  x=labels_anom_mask,
                  y=predicted_normals[threshold, :]),
              elems=tf.range(start=0, limit=num_thresh, dtype=tf.int64),
              dtype=tf.bool),
          dtype=tf.int64),
      axis=1)

  fp = tf.reduce_sum(
      input_tensor=tf.cast(
          x=tf.map_fn(
              fn=lambda threshold: tf.logical_and(
                  x=labels_norm_mask,
                  y=predicted_anomalies[threshold, :]),
              elems=tf.range(start=0, limit=num_thresh, dtype=tf.int64),
              dtype=tf.bool),
          dtype=tf.int64),
      axis=1)

  tn = tf.reduce_sum(
      input_tensor=tf.cast(
          x=tf.map_fn(
              fn=lambda threshold: tf.logical_and(
                  x=labels_norm_mask,
                  y=predicted_normals[threshold, :]),
              elems=tf.range(start=0, limit=num_thresh, dtype=tf.int64),
              dtype=tf.bool),
          dtype=tf.int64),
      axis=1)

  if mode == tf.estimator.ModeKeys.EVAL:
    # shape = ()
    tp = tf.squeeze(input=tp)
    fn = tf.squeeze(input=fn)
    fp = tf.squeeze(input=fp)
    tn = tf.squeeze(input=tn)

  with tf.control_dependencies(
      control_inputs=[tf.assign_add(ref=tp_at_thresh_var, value=tp),
                      tf.assign_add(ref=fn_at_thresh_var, value=fn),
                      tf.assign_add(ref=fp_at_thresh_var, value=fp),
                      tf.assign_add(ref=tn_at_thresh_var, value=tn)]):

    return (tf.identity(input=tp_at_thresh_var),
            tf.identity(input=fn_at_thresh_var),
            tf.identity(input=fp_at_thresh_var),
            tf.identity(input=tn_at_thresh_var))


def calculate_composite_classification_metrics(tp, fn, fp, tn, f_score_beta):
  """Calculates compositive classification metrics from the confusion matrix.

  Given variables for the confusion matrix and the value of beta for f-beta
  score, returns accuracy, precision, recall, and f-beta score composite
  metrics.

  Args:
    tp: tf.int64 variable tracking number of true positives at
      each possible anomaly threshold.
    fn: tf.int64 variable tracking number of false negatives at
      each possible anomaly threshold.
    fp: tf.int64 variable tracking number of false positives at
      each possible anomaly threshold.
    tn: tf.int64 variable tracking number of true negatives at
      each possible anomaly threshold.
    f_score_beta: Value of beta for f-beta score.

  Returns:
    Accuracy, precision, recall, and f-beta score composite metric tensors.
  """
  # time_shape = (num_time_anom_thresh,)
  # feat_shape = (num_feat_anom_thresh,)
  acc = tf.cast(x=tp + tn, dtype=tf.float64) \
    / tf.cast(x=tp + fn + fp + tn, dtype=tf.float64)
  tp_float64 = tf.cast(x=tp, dtype=tf.float64)
  pre = tp_float64 / tf.cast(x=tp + fp, dtype=tf.float64)
  rec = tp_float64 / tf.cast(x=tp + fn, dtype=tf.float64)
  f_beta_numerator = (1.0 + f_score_beta ** 2) * (pre * rec)
  f_beta_score = f_beta_numerator / (f_score_beta ** 2 * pre + rec)

  return acc, pre, rec, f_beta_score


def find_best_anom_thresh(
    anom_threshs, f_beta_score, user_passed_anom_thresh, anom_thresh_var):
  """Find best anomaly threshold to use for anomaly classification.

  Given grid of anomaly thresholds, variables for the confusion matrix, and the
  value of beta for f-beta score, returns accuracy, precision, recall, and
  f-beta score composite metrics.

  Args:
    anom_threshs: tf.float64 vector tensor of grid of anomaly thresholds to try.
    f_beta_score: tf.float64 vector tensor of f-beta scores for each anomaly
      threshold.
    user_passed_anom_thresh: User passed anomaly threshold that overrides
      the threshold optimization.
    anom_thresh_var: tf.float64 variable that stores anomaly threshold value.

  Returns:
    Updated variable that stores the anomaly threshold value
  """
  if user_passed_anom_thresh is None:
    # shape = ()
    best_anom_thresh = tf.gather(
        params=anom_threshs, indices=tf.argmax(input=f_beta_score, axis=0))
  else:
    # shape = ()
    best_anom_thresh = user_passed_anom_thresh

  with tf.control_dependencies(
      control_inputs=[tf.assign(
          ref=anom_thresh_var, value=best_anom_thresh)]):

    return tf.identity(input=anom_thresh_var)


def tune_anomaly_thresholds_supervised_training(
    labels_norm_mask,
    labels_anom_mask,
    mahalanobis_dist_time,
    tp_thresh_time_var,
    fn_thresh_time_var,
    fp_thresh_time_var,
    tn_thresh_time_var,
    time_anom_thresh_var,
    mahalanobis_dist_feat,
    tp_thresh_feat_var,
    fn_thresh_feat_var,
    fp_thresh_feat_var,
    tn_thresh_feat_var,
    feat_anom_thresh_var,
    params,
    mode,
    dummy_var):
  """Tunes anomaly thresholds during supervised training mode.

  Given label masks, mahalanobis distances, confusion matrices, and anomaly
  thresholds, returns loss and train_op.

  Args:
    labels_norm_mask: tf.bool vector mask of labels for normals.
    labels_anom_mask: tf.bool vector mask of labels for anomalies.
    mahalanobis_dist_time: Mahalanobis distance, time major.
    tp_thresh_time_var: tf.int64 variable to track number of true positives wrt
      thresholds for time major case.
    fn_thresh_time_var: tf.int64 variable to track number of false negatives wrt
      thresholds for time major case.
    fp_thresh_time_var: tf.int64 variable to track number of false positives wrt
      thresholds for time major case.
    tn_thresh_time_var: tf.int64 variable to track number of true negatives wrt
      thresholds for time major case.
    time_anom_thresh_var: tf.float64 variable to hold the set time anomaly
      threshold.
    mahalanobis_dist_feat: Mahalanobis distance, features major.
    tp_thresh_feat_var: tf.int64 variable to track number of true positives wrt
      thresholds for feat major case.
    fn_thresh_feat_var: tf.int64 variable to track number of false negatives wrt
      thresholds for feat major case.
    fp_thresh_feat_var: tf.int64 variable to track number of false positives wrt
      thresholds for feat major case.
    tn_thresh_feat_var: tf.int64 variable to track number of true negatives wrt
      thresholds for feat major case.
    feat_anom_thresh_var: tf.float64 variable to hold the set feat anomaly
      threshold.
    params: Dictionary of parameters.
    mode: Estimator ModeKeys. Can take value of only TRAIN.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: The scalar loss to tie our updates back to Estimator graph.
    train_op: The train operation to tie our updates back to Estimator graph.
  """
  # Time based
  # shape = (num_time_anom_thresh,)
  time_anom_threshs = tf.linspace(
      start=tf.constant(
          value=params["min_time_anom_thresh"], dtype=tf.float64),
      stop=tf.constant(
          value=params["max_time_anom_thresh"], dtype=tf.float64),
      num=params["num_time_anom_thresh"])

  with tf.variable_scope(
      name_or_scope="mahalanobis_dist_thresh_vars",
      reuse=tf.AUTO_REUSE):
    (tp_time_update_op,
     fn_time_update_op,
     fp_time_update_op,
     tn_time_update_op) = \
      update_anom_thresh_vars(
          labels_norm_mask,
          labels_anom_mask,
          params["num_time_anom_thresh"],
          time_anom_threshs,
          mahalanobis_dist_time,
          tp_thresh_time_var,
          fn_thresh_time_var,
          fp_thresh_time_var,
          tn_thresh_time_var,
          mode)

  # Features based
  # shape = (num_feat_anom_thresh,)
  feat_anom_threshs = tf.linspace(
      start=tf.constant(value=params["min_feat_anom_thresh"],
                        dtype=tf.float64),
      stop=tf.constant(value=params["max_feat_anom_thresh"],
                       dtype=tf.float64),
      num=params["num_feat_anom_thresh"])

  with tf.variable_scope(
      name_or_scope="mahalanobis_dist_thresh_vars",
      reuse=tf.AUTO_REUSE):
    (tp_feat_update_op,
     fn_feat_update_op,
     fp_feat_update_op,
     tn_feat_update_op) = \
      update_anom_thresh_vars(
          labels_norm_mask,
          labels_anom_mask,
          params["num_feat_anom_thresh"],
          feat_anom_threshs,
          mahalanobis_dist_feat,
          tp_thresh_feat_var,
          fn_thresh_feat_var,
          fp_thresh_feat_var,
          tn_thresh_feat_var,
          mode)

  # Reconstruction loss on evaluation set
  with tf.control_dependencies(
      control_inputs=[
          tp_time_update_op,
          fn_time_update_op,
          fp_time_update_op,
          tn_time_update_op,
          tp_feat_update_op,
          fn_feat_update_op,
          fp_feat_update_op,
          tn_feat_update_op]):
    # Time based
    _, pre_time, rec_time, f_beta_time = \
      calculate_composite_classification_metrics(
          tp_thresh_time_var,
          fn_thresh_time_var,
          fp_thresh_time_var,
          tn_thresh_time_var,
          params["f_score_beta"])

    # Features based
    _, pre_feat, rec_feat, f_beta_feat = \
      calculate_composite_classification_metrics(
          tp_thresh_feat_var,
          fn_thresh_feat_var,
          fp_thresh_feat_var,
          tn_thresh_feat_var,
          params["f_score_beta"])

    with tf.control_dependencies(
        control_inputs=[pre_time, pre_feat, rec_time, rec_feat]):
      with tf.control_dependencies(
          control_inputs=[f_beta_time, f_beta_feat]):
        # Time based
        best_anom_thresh_time = find_best_anom_thresh(
            time_anom_threshs,
            f_beta_time,
            params["time_anom_thresh"],
            time_anom_thresh_var)

        # Features based
        best_anom_thresh_feat = find_best_anom_thresh(
            feat_anom_threshs,
            f_beta_feat,
            params["feat_anom_thresh"],
            feat_anom_thresh_var)

        with tf.control_dependencies(
            control_inputs=[best_anom_thresh_time,
                            best_anom_thresh_feat]):
          loss = tf.reduce_sum(
              input_tensor=tf.zeros(
                  shape=(), dtype=tf.float64) * dummy_var)

          train_op = tf.contrib.layers.optimize_loss(
              loss=loss,
              global_step=tf.train.get_global_step(),
              learning_rate=params["learning_rate"],
              optimizer="SGD")

  return loss, train_op


def tune_anomaly_thresholds_evaluation(
    labels_norm_mask,
    labels_anom_mask,
    time_anom_thresh_var,
    mahalanobis_dist_time,
    tp_thresh_eval_time_var,
    fn_thresh_eval_time_var,
    fp_thresh_eval_time_var,
    tn_thresh_eval_time_var,
    feat_anom_thresh_var,
    mahalanobis_dist_feat,
    tp_thresh_eval_feat_var,
    fn_thresh_eval_feat_var,
    fp_thresh_eval_feat_var,
    tn_thresh_eval_feat_var,
    params,
    mode):
  """Checks tuned anomaly thresholds during evaluation mode.

  Given label masks, mahalanobis distances, confusion matrices, and anomaly
  thresholds, returns loss and eval_metric_ops.

  Args:
    labels_norm_mask: tf.bool vector mask of labels for normals.
    labels_anom_mask: tf.bool vector mask of labels for anomalies.
    time_anom_thresh_var: tf.float64 scalar time anomaly threshold value.
    mahalanobis_dist_time: Mahalanobis distance, time major.
    tp_thresh_eval_time_var: tf.int64 variable to track number of true
      positives wrt thresholds for time major case for evaluation.
    fn_thresh_eval_time_var: tf.int64 variable to track number of false
      negatives wrt thresholds for time major case for evaluation.
    fp_thresh_eval_time_var: tf.int64 variable to track number of false
      positives wrt thresholds for time major case for evaluation.
    tn_thresh_eval_time_var: tf.int64 variable to track number of true
      negatives wrt thresholds for time major case for evaluation.
    feat_anom_thresh_var: tf.float64 scalar feature anomaly threshold value.
    mahalanobis_dist_feat: Mahalanobis distance, features major.
    tp_thresh_eval_feat_var: tf.int64 variable to track number of true
      positives wrt thresholds for feat major case for evaluation.
    fn_thresh_eval_feat_var: tf.int64 variable to track number of false
      negatives wrt thresholds for feat major case for evaluation.
    fp_thresh_eval_feat_var: tf.int64 variable to track number of false
      positives wrt thresholds for feat major case for evaluation.
    tn_thresh_eval_feat_var: tf.int64 variable to track number of true
      negatives wrt thresholds for feat major case for evaluation.
    params: Dictionary of parameters.
    mode: Estimator ModeKeys. Can take value of only EVAL.

  Returns:
    loss: Scalar reconstruction loss.
    eval_metric_ops: Evaluation metrics of reconstruction.
  """
  with tf.variable_scope(
      name_or_scope="anom_thresh_eval_vars", reuse=tf.AUTO_REUSE):
    # Time based
    (tp_time_update_op,
     fn_time_update_op,
     fp_time_update_op,
     tn_time_update_op) = \
      update_anom_thresh_vars(
          labels_norm_mask,
          labels_anom_mask,
          1,
          time_anom_thresh_var,
          mahalanobis_dist_time,
          tp_thresh_eval_time_var,
          fn_thresh_eval_time_var,
          fp_thresh_eval_time_var,
          tn_thresh_eval_time_var,
          mode)

    # Features based
    (tp_feat_update_op,
     fn_feat_update_op,
     fp_feat_update_op,
     tn_feat_update_op) = \
      update_anom_thresh_vars(
          labels_norm_mask,
          labels_anom_mask,
          1,
          feat_anom_thresh_var,
          mahalanobis_dist_feat,
          tp_thresh_eval_feat_var,
          fn_thresh_eval_feat_var,
          fp_thresh_eval_feat_var,
          tn_thresh_eval_feat_var,
          mode)

  with tf.variable_scope(
      name_or_scope="anom_thresh_eval_vars", reuse=tf.AUTO_REUSE):
    # Time based
    (acc_time_update_op,
     pre_time_update_op,
     rec_time_update_op,
     f_beta_time_update_op) = \
      calculate_composite_classification_metrics(
          tp_thresh_eval_time_var,
          fn_thresh_eval_time_var,
          fp_thresh_eval_time_var,
          tn_thresh_eval_time_var,
          params["f_score_beta"])

    # Features based
    (acc_feat_update_op,
     pre_feat_update_op,
     rec_feat_update_op,
     f_beta_feat_update_op) = \
      calculate_composite_classification_metrics(
          tp_thresh_eval_feat_var,
          fn_thresh_eval_feat_var,
          fp_thresh_eval_feat_var,
          tn_thresh_eval_feat_var,
          params["f_score_beta"])

  loss = tf.zeros(shape=[], dtype=tf.float64)

  # Time based
  acc_trues = tf.cast(
      x=tp_thresh_eval_time_var + tn_thresh_eval_time_var,
      dtype=tf.float64)
  acc_falses = tf.cast(
      x=fp_thresh_eval_time_var + fn_thresh_eval_time_var,
      dtype=tf.float64)
  acc_thresh_eval_time_var = acc_trues / (acc_trues + acc_falses)

  tp_float = tf.cast(x=tp_thresh_eval_time_var, dtype=tf.float64)

  pre_denominator = tf.cast(
      x=tp_thresh_eval_time_var + fp_thresh_eval_time_var,
      dtype=tf.float64)
  pre_thresh_eval_time_var = tp_float / pre_denominator

  rec_denominator = tf.cast(
      x=tp_thresh_eval_time_var + fn_thresh_eval_time_var,
      dtype=tf.float64)
  rec_thresh_eval_time_var = tp_float / rec_denominator

  f_beta_numerator = (1.0 + params["f_score_beta"] ** 2)
  f_beta_numerator *= pre_thresh_eval_time_var
  f_beta_numerator *= rec_thresh_eval_time_var
  f_beta_denominator = params["f_score_beta"] ** 2
  f_beta_denominator *= pre_thresh_eval_time_var
  f_beta_denominator += rec_thresh_eval_time_var
  f_beta_thresh_eval_time_var = f_beta_numerator / f_beta_denominator

  # Features based
  acc_trues = tf.cast(
      x=tp_thresh_eval_feat_var + tn_thresh_eval_feat_var,
      dtype=tf.float64)
  acc_falses = tf.cast(
      x=fp_thresh_eval_feat_var + fn_thresh_eval_feat_var,
      dtype=tf.float64)
  acc_thresh_eval_feat_var = acc_trues / (acc_trues + acc_falses)

  tp_float = tf.cast(x=tp_thresh_eval_feat_var, dtype=tf.float64)

  pre_denominator = tf.cast(
      x=tp_thresh_eval_feat_var + fp_thresh_eval_feat_var,
      dtype=tf.float64)
  pre_thresh_eval_feat_var = tp_float / pre_denominator

  rec_denominator = tf.cast(
      x=tp_thresh_eval_feat_var + fn_thresh_eval_feat_var,
      dtype=tf.float64)
  rec_thresh_eval_feat_var = tp_float / rec_denominator

  f_beta_numerator = (1.0 + params["f_score_beta"] ** 2)
  f_beta_numerator *= pre_thresh_eval_feat_var
  f_beta_numerator *= rec_thresh_eval_feat_var
  f_beta_denominator = params["f_score_beta"] ** 2
  f_beta_denominator *= pre_thresh_eval_feat_var
  f_beta_denominator += rec_thresh_eval_feat_var
  f_beta_thresh_eval_feat_var = f_beta_numerator / f_beta_denominator

  # Anomaly detection eval metrics
  eval_metric_ops = {
      # Time based
      "time_anom_tp": (tp_thresh_eval_time_var, tp_time_update_op),
      "time_anom_fn": (fn_thresh_eval_time_var, fn_time_update_op),
      "time_anom_fp": (fp_thresh_eval_time_var, fp_time_update_op),
      "time_anom_tn": (tn_thresh_eval_time_var, tn_time_update_op),

      "time_anom_acc": (acc_thresh_eval_time_var, acc_time_update_op),
      "time_anom_pre": (pre_thresh_eval_time_var, pre_time_update_op),
      "time_anom_rec": (rec_thresh_eval_time_var, rec_time_update_op),
      "time_anom_f_beta": (f_beta_thresh_eval_time_var,
                           f_beta_time_update_op),

      # Features based
      "feat_anom_tp": (tp_thresh_eval_feat_var, tp_feat_update_op),
      "feat_anom_fn": (fn_thresh_eval_feat_var, fn_feat_update_op),
      "feat_anom_fp": (fp_thresh_eval_feat_var, fp_feat_update_op),
      "feat_anom_tn": (tn_thresh_eval_feat_var, tn_feat_update_op),

      "feat_anom_acc": (acc_thresh_eval_feat_var, acc_feat_update_op),
      "feat_anom_pre": (pre_thresh_eval_feat_var, pre_feat_update_op),
      "feat_anom_rec": (rec_thresh_eval_feat_var, rec_feat_update_op),
      "feat_anom_f_beta": (f_beta_thresh_eval_feat_var,
                           f_beta_feat_update_op)
  }

  return loss, eval_metric_ops


def tune_anomaly_thresholds_unsupervised_training(
    cur_batch_size,
    num_feat,
    time_anom_thresh_var,
    mahalanobis_dist_time,
    count_thresh_time_var,
    mean_thresh_time_var,
    var_thresh_time_var,
    feat_anom_thresh_var,
    mahalanobis_dist_feat,
    count_thresh_feat_var,
    mean_thresh_feat_var,
    var_thresh_feat_var,
    params,
    dummy_var):
  """Calculates error distribution statistics during training mode.

  Given dimensions of inputs, mahalanobis distances, and variables tracking
  counts, means, and variances of mahalanobis distance, returns loss and
  train_op.

  Args:
    cur_batch_size: Current batch size, could be partially filled.
    num_feat: Number of features.
    time_anom_thresh_var: Time anomaly threshold variable.
    mahalanobis_dist_time: Time major mahalanobis distance.
    count_thresh_time_var: Time major running count of number of records.
    mean_thresh_time_var: Time major running mean of mahalanobis distance.
    var_thresh_time_var: Time major running variance of mahalanobis distance.
    feat_anom_thresh_var: Feature anomaly threshold variable.
    mahalanobis_dist_feat: Feature major mahalanobis distance.
    count_thresh_feat_var: Feature major running count of number of records.
    mean_thresh_feat_var: Feature major running mean of mahalanobis distance.
    var_thresh_feat_var: Feature major running variance of mahalanobis distance.
    params: Dictionary of parameters.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: The scalar loss to tie our updates back to Estimator graph.
    train_op: The train operation to tie our updates back to Estimator graph.
  """
  with tf.variable_scope(
      name_or_scope="mahalanobis_dist_thresh_vars", reuse=tf.AUTO_REUSE):
    # Time based
    mahalanobis_dist_time_flat = tf.reshape(
        tensor=mahalanobis_dist_time,
        shape=[cur_batch_size * params["seq_len"]])

    singleton_time_condition = tf.equal(
        x=cur_batch_size * params["seq_len"], y=1)

    var_time_var, mean_time_var, count_time_var = tf.cond(
        pred=singleton_time_condition,
        true_fn=lambda: singleton_batch_var_variable_updating(
            params["seq_len"],
            mahalanobis_dist_time_flat,
            count_thresh_time_var,
            mean_thresh_time_var,
            var_thresh_time_var),
        false_fn=lambda: non_singleton_batch_var_variable_updating(
            cur_batch_size,
            params["seq_len"],
            mahalanobis_dist_time_flat,
            count_thresh_time_var,
            mean_thresh_time_var,
            var_thresh_time_var))

    # Features based
    mahalanobis_dist_feat_flat = tf.reshape(
        tensor=mahalanobis_dist_feat,
        shape=[cur_batch_size * num_feat])

    singleton_feat_condition = tf.equal(
        x=cur_batch_size * num_feat, y=1)

    var_feat_var, mean_feat_var, count_feat_var = tf.cond(
        pred=singleton_feat_condition,
        true_fn=lambda: singleton_batch_var_variable_updating(
            num_feat,
            mahalanobis_dist_feat_flat,
            count_thresh_feat_var,
            mean_thresh_feat_var,
            var_thresh_feat_var),
        false_fn=lambda: non_singleton_batch_var_variable_updating(
            cur_batch_size,
            num_feat,
            mahalanobis_dist_feat_flat,
            count_thresh_feat_var,
            mean_thresh_feat_var,
            var_thresh_feat_var))

  # Lastly use control dependencies around loss to enforce the mahalanobis
  # variables to be assigned, the control order matters, hence the separate
  # contexts.
  with tf.control_dependencies(
      control_inputs=[var_time_var, var_feat_var]):
    with tf.control_dependencies(
        control_inputs=[mean_time_var, mean_feat_var]):
      with tf.control_dependencies(
          control_inputs=[count_time_var, count_feat_var]):
        time_out = mean_time_var
        time_out += params["time_thresh_scl"] * tf.sqrt(x=var_time_var)
        feat_out = mean_feat_var
        feat_out += params["feat_thresh_scl"] * tf.sqrt(x=var_feat_var)
        with tf.control_dependencies(
            control_inputs=[tf.assign(ref=time_anom_thresh_var,
                                      value=time_out),
                            tf.assign(ref=feat_anom_thresh_var,
                                      value=feat_out)]):

          loss = tf.reduce_sum(
              input_tensor=tf.zeros(shape=(), dtype=tf.float64) * dummy_var)

          train_op = tf.contrib.layers.optimize_loss(
              loss=loss,
              global_step=tf.train.get_global_step(),
              learning_rate=params["learning_rate"],
              optimizer="SGD")

  return loss, train_op


def anomaly_detection_predictions(
    cur_batch_size,
    seq_len,
    num_feat,
    mahalanobis_dist_time,
    mahalanobis_dist_feat,
    time_anom_thresh_var,
    feat_anom_thresh_var,
    X_time_abs_recon_err,
    X_feat_abs_recon_err):
  """Creates Estimator predictions and export outputs.

  Given dimensions of inputs, mahalanobis distances and their respective
  thresholds, and reconstructed inputs' absolute errors, returns Estimator's
  predictions and export outputs.

  Args:
    cur_batch_size: Current batch size, could be partially filled.
    seq_len: Number of timesteps in sequence.
    num_feat: Number of features.
    mahalanobis_dist_time: Mahalanobis distance, time major.
    mahalanobis_dist_feat: Mahalanobis distance, features major.
    time_anom_thresh_var: Time anomaly threshold variable.
    feat_anom_thresh_var: Features anomaly threshold variable.
    X_time_abs_recon_err: Time major reconstructed input data's absolute
      reconstruction error.
    X_feat_abs_recon_err: Features major reconstructed input data's absolute
      reconstruction error.

  Returns:
    predictions_dict: Dictionary of predictions to output for local prediction.
    export_outputs: Dictionary to output from exported model for serving.
  """
  # Flag predictions as either normal or anomalous
  # shape = (cur_batch_size,)
  time_anom_flags = tf.where(
      condition=tf.reduce_any(
          input_tensor=tf.greater(
              x=tf.abs(x=mahalanobis_dist_time),
              y=time_anom_thresh_var),
          axis=1),
      x=tf.ones(shape=[cur_batch_size], dtype=tf.int64),
      y=tf.zeros(shape=[cur_batch_size], dtype=tf.int64))

  # shape = (cur_batch_size,)
  feat_anom_flags = tf.where(
      condition=tf.reduce_any(
          input_tensor=tf.greater(
              x=tf.abs(x=mahalanobis_dist_feat),
              y=feat_anom_thresh_var),
          axis=1),
      x=tf.ones(shape=[cur_batch_size], dtype=tf.int64),
      y=tf.zeros(shape=[cur_batch_size], dtype=tf.int64))

  # Create predictions dictionary
  predictions_dict = {
      "X_time_abs_recon_err": tf.reshape(
          tensor=X_time_abs_recon_err,
          shape=[cur_batch_size, seq_len, num_feat]),
      "X_feat_abs_recon_err": tf.transpose(
          a=tf.reshape(
              tensor=X_feat_abs_recon_err,
              shape=[cur_batch_size, num_feat, seq_len]),
          perm=[0, 2, 1]),
      "mahalanobis_dist_time": mahalanobis_dist_time,
      "mahalanobis_dist_feat": mahalanobis_dist_feat,
      "time_anom_flags": time_anom_flags,
      "feat_anom_flags": feat_anom_flags}

  # Create export outputs
  export_outputs = {
      "predict_export_outputs": tf.estimator.export.PredictOutput(
          outputs=predictions_dict)
  }

  return predictions_dict, export_outputs


# Create our model function to be used in our custom estimator
def anomaly_detection(features, labels, mode, params):
  """Custom Estimator model function for anomaly detection.

  Given dictionary of feature tensors, labels tensor, Estimator mode, and
  dictionary for parameters, return EstimatorSpec object for custom Estimator.

  Args:
    features: Dictionary of feature tensors.
    labels: Labels tensor or None.
    mode: Estimator ModeKeys. Can take values of TRAIN, EVAL, and PREDICT.
    params: Dictionary of parameters.

  Returns:
    EstimatorSpec object.
  """
  print("\nanomaly_detection: features = \n{}".format(features))
  print("anomaly_detection: labels = \n{}".format(labels))
  print("anomaly_detection: mode = \n{}".format(mode))
  print("anomaly_detection: params = \n{}".format(params))

  # Get input sequence tensor into correct shape
  # Get dynamic batch size in case there was a partially filled batch
  cur_batch_size = tf.shape(
      input=features[UNLABELED_CSV_COLUMNS[0]], out_type=tf.int64)[0]

  # Get the number of features
  num_feat = len(UNLABELED_CSV_COLUMNS)

  # Stack all of the features into a 3-D tensor
  # shape = (cur_batch_size, seq_len, num_feat)
  X = tf.stack(
      values=[features[key] for key in UNLABELED_CSV_COLUMNS], axis=2)

  ##############################################################################

  # Variables for calculating error distribution statistics
  (abs_err_count_time_var,
   abs_err_mean_time_var,
   abs_err_cov_time_var,
   abs_err_inv_cov_time_var,
   abs_err_count_feat_var,
   abs_err_mean_feat_var,
   abs_err_cov_feat_var,
   abs_err_inv_cov_feat_var) = create_both_mahalanobis_dist_vars(
       seq_len=params["seq_len"], num_feat=num_feat)

  # Variables for automatically tuning anomaly thresh
  if params["labeled_tune_thresh"]:
    (tp_thresh_time_var,
     fn_thresh_time_var,
     fp_thresh_time_var,
     tn_thresh_time_var,
     tp_thresh_feat_var,
     fn_thresh_feat_var,
     fp_thresh_feat_var,
     tn_thresh_feat_var) = create_both_confusion_matrix_thresh_vars(
         scope="mahalanobis_dist_thresh_vars",
         time_thresh_size=[params["num_time_anom_thresh"]],
         feat_thresh_size=[params["num_feat_anom_thresh"]])
  else:
    (count_thresh_time_var,
     mean_thresh_time_var,
     var_thresh_time_var,
     count_thresh_feat_var,
     mean_thresh_feat_var,
     var_thresh_feat_var) = create_both_mahalanobis_unsupervised_thresh_vars(
         scope="mahalanobis_dist_thresh_vars")

  with tf.variable_scope(
      name_or_scope="mahalanobis_dist_thresh_vars", reuse=tf.AUTO_REUSE):
    time_anom_thresh_var = tf.get_variable(
        name="time_anom_thresh_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[], dtype=tf.float64),
        trainable=False)

    feat_anom_thresh_var = tf.get_variable(
        name="feat_anom_thresh_var",
        dtype=tf.float64,
        initializer=tf.zeros(shape=[], dtype=tf.float64),
        trainable=False)

  # Variables for tuning anomaly thresh evaluation
  if params["labeled_tune_thresh"]:
    (tp_thresh_eval_time_var,
     fn_thresh_eval_time_var,
     fp_thresh_eval_time_var,
     tn_thresh_eval_time_var,
     tp_thresh_eval_feat_var,
     fn_thresh_eval_feat_var,
     fp_thresh_eval_feat_var,
     tn_thresh_eval_feat_var) = create_both_confusion_matrix_thresh_vars(
         scope="anom_thresh_eval_vars", time_thresh_size=[], feat_thresh_size=[])

  # Create dummy variable for graph dependency requiring a gradient for TRAIN
  dummy_var = tf.get_variable(
      name="dummy_var",
      dtype=tf.float64,
      initializer=tf.zeros(shape=[], dtype=tf.float64),
      trainable=True)

################################################################################

  predictions_dict = None
  loss = None
  train_op = None
  eval_metric_ops = None
  export_outputs = None

  # Now branch off based on which mode we are in

  # Call specific model
  model_functions = {
      "dense_autoencoder": dense_autoencoder_model,
      "lstm_enc_dec_autoencoder": lstm_enc_dec_autoencoder_model,
      "pca": pca_model}

  # Get function pointer for selected model type
  model_function = model_functions[params["model_type"]]

  # Build selected model
  loss, train_op, X_time_orig, X_time_recon, X_feat_orig, X_feat_recon = \
    model_function(X, mode, params, cur_batch_size, num_feat, dummy_var)

  if not (mode == tf.estimator.ModeKeys.TRAIN and
          params["training_mode"] == "reconstruction"):
    # shape = (cur_batch_size * seq_len, num_feat)
    X_time_abs_recon_err = tf.abs(
        x=X_time_orig - X_time_recon)

    # Features based
    # shape = (cur_batch_size * num_feat, seq_len)
    X_feat_abs_recon_err = tf.abs(
        x=X_feat_orig - X_feat_recon)

    if (mode == tf.estimator.ModeKeys.TRAIN and
        params["training_mode"] == "calculate_error_distribution_statistics"):
      loss, train_op = calculate_error_distribution_statistics_training(
          cur_batch_size,
          num_feat,
          X_time_abs_recon_err,
          abs_err_count_time_var,
          abs_err_mean_time_var,
          abs_err_cov_time_var,
          abs_err_inv_cov_time_var,
          X_feat_abs_recon_err,
          abs_err_count_feat_var,
          abs_err_mean_feat_var,
          abs_err_cov_feat_var,
          abs_err_inv_cov_feat_var,
          params,
          dummy_var)
    elif (mode == tf.estimator.ModeKeys.EVAL and
          params["training_mode"] != "tune_anomaly_thresholds"):
      loss, eval_metric_ops = reconstruction_evaluation(
          X_time_orig, X_time_recon, params["training_mode"])
    elif (mode == tf.estimator.ModeKeys.PREDICT or
          ((mode == tf.estimator.ModeKeys.TRAIN or
            mode == tf.estimator.ModeKeys.EVAL) and
           params["training_mode"] == "tune_anomaly_thresholds")):
      with tf.variable_scope(
          name_or_scope="mahalanobis_dist_vars", reuse=tf.AUTO_REUSE):
        # Time based
        # shape = (cur_batch_size, seq_len)
        mahalanobis_dist_time = mahalanobis_dist(
            err_vec=X_time_abs_recon_err,
            mean_vec=abs_err_mean_time_var,
            inv_cov=abs_err_inv_cov_time_var,
            final_shape=params["seq_len"])

        # Features based
        # shape = (cur_batch_size, num_feat)
        mahalanobis_dist_feat = mahalanobis_dist(
            err_vec=X_feat_abs_recon_err,
            mean_vec=abs_err_mean_feat_var,
            inv_cov=abs_err_inv_cov_feat_var,
            final_shape=num_feat)

      if mode != tf.estimator.ModeKeys.PREDICT:
        if params["labeled_tune_thresh"]:
          labels_norm_mask = tf.equal(x=labels, y=0)
          labels_anom_mask = tf.equal(x=labels, y=1)

          if mode == tf.estimator.ModeKeys.TRAIN:
            loss, train_op = tune_anomaly_thresholds_supervised_training(
                labels_norm_mask,
                labels_anom_mask,
                mahalanobis_dist_time,
                tp_thresh_time_var,
                fn_thresh_time_var,
                fp_thresh_time_var,
                tn_thresh_time_var,
                time_anom_thresh_var,
                mahalanobis_dist_feat,
                tp_thresh_feat_var,
                fn_thresh_feat_var,
                fp_thresh_feat_var,
                tn_thresh_feat_var,
                feat_anom_thresh_var,
                params,
                mode,
                dummy_var)
          elif mode == tf.estimator.ModeKeys.EVAL:
            loss, eval_metric_ops = tune_anomaly_thresholds_evaluation(
                labels_norm_mask,
                labels_anom_mask,
                time_anom_thresh_var,
                mahalanobis_dist_time,
                tp_thresh_eval_time_var,
                fn_thresh_eval_time_var,
                fp_thresh_eval_time_var,
                tn_thresh_eval_time_var,
                feat_anom_thresh_var,
                mahalanobis_dist_feat,
                tp_thresh_eval_feat_var,
                fn_thresh_eval_feat_var,
                fp_thresh_eval_feat_var,
                tn_thresh_eval_feat_var,
                params,
                mode)
        else:  # not params["labeled_tune_thresh"]
          if mode == tf.estimator.ModeKeys.TRAIN:
            loss, train_op = tune_anomaly_thresholds_unsupervised_training(
                cur_batch_size,
                num_feat,
                time_anom_thresh_var,
                mahalanobis_dist_time,
                count_thresh_time_var,
                mean_thresh_time_var,
                var_thresh_time_var,
                feat_anom_thresh_var,
                mahalanobis_dist_feat,
                count_thresh_feat_var,
                mean_thresh_feat_var,
                var_thresh_feat_var,
                params,
                dummy_var)
      else:  # mode == tf.estimator.ModeKeys.PREDICT
        predictions_dict, export_outputs = anomaly_detection_predictions(
            cur_batch_size,
            params["seq_len"],
            num_feat,
            mahalanobis_dist_time,
            mahalanobis_dist_feat,
            time_anom_thresh_var,
            feat_anom_thresh_var,
            X_time_abs_recon_err,
            X_feat_abs_recon_err)

  # Return EstimatorSpec
  return tf.estimator.EstimatorSpec(
      mode=mode,
      predictions=predictions_dict,
      loss=loss,
      train_op=train_op,
      eval_metric_ops=eval_metric_ops,
      export_outputs=export_outputs)


# Serving input functions
def fix_shape_and_type_for_serving(placeholder):
  """Fixes the shape and type of serving input strings.

  Given placeholder tensor, return parsed and processed feature tensor.

  Args:
    placeholder: Placeholder tensor holding raw data from serving input
      function.

  Returns:
    Parsed and processed feature tensor.
  """
  cur_batch_size = tf.shape(input=placeholder, out_type=tf.int64)[0]

  # String split each string in batch and output values from the resulting
  # SparseTensors
  # shape = (batch_size, seq_len)
  split_string = tf.stack(values=tf.map_fn(
      fn=lambda x: tf.string_split(
          source=[placeholder[x]], delimiter=",").values,
      elems=tf.range(
          start=0, limit=cur_batch_size, dtype=tf.int64),
      dtype=tf.string), axis=0)

  # Convert each string in the split tensor to float
  # shape = (batch_size, seq_len)
  feature_tensor = tf.string_to_number(
      string_tensor=split_string, out_type=tf.float64)

  return feature_tensor


def get_shape_and_set_modified_shape_2D(tensor, additional_dimension_sizes):
  """Fixes the shape and type of serving input strings.

  Given feature tensor and additional dimension size, sequence length,
  fixes dynamic shape ambiguity of last dimension so that we will be able to
  use it in our DNN (since tf.layers.dense require the last dimension to be
  known).

  Args:
    tensor: tf.float64 vector feature tensor.
    additional_dimension_sizes: Additional dimension size, namely sequence
      length.

  Returns:
    Feature tensor with set static shape for sequence length.
  """
  # Get static shape for tensor and convert it to list
  shape = tensor.get_shape().as_list()
  # Set outer shape to additional_dimension_sizes[0] since know this is the
  # correct size
  shape[1] = additional_dimension_sizes[0]
  # Set the shape of tensor to our modified shape
  # shape = (batch_size, additional_dimension_sizes[0])
  tensor.set_shape(shape=shape)

  return tensor


def serving_input_fn(seq_len):
  """Serving input function.

  Given the sequence length, return ServingInputReceiver object.

  Args:
    seq_len: Number of timesteps in sequence.

  Returns:
    ServingInputReceiver object containing features and receiver tensors.
  """
  # Create placeholders to accept the data sent to the model at serving time
  # All features come in as a batch of strings, shape = (batch_size,),
  # this was so because of passing the arrays to online ml-engine prediction
  feature_placeholders = {
      feature: tf.placeholder(
          dtype=tf.string, shape=[None])
      for feature in UNLABELED_CSV_COLUMNS
  }

  # Create feature tensors
  features = {key: fix_shape_and_type_for_serving(placeholder=tensor)
              for key, tensor in feature_placeholders.items()}

  # Fix dynamic shape ambiguity of feature tensors for our DNN
  features = {key: get_shape_and_set_modified_shape_2D(
      tensor=tensor, additional_dimension_sizes=[seq_len])
              for key, tensor in features.items()}

  return tf.estimator.export.ServingInputReceiver(
      features=features, receiver_tensors=feature_placeholders)


def train_and_evaluate(args):
  """Train and evaluate custom Estimator with three training modes.

  Given the dictionary of parameters, create custom Estimator and run up to
  three training modes then return Estimator object.

  Args:
    args: Dictionary of parameters.

  Returns:
    Estimator object.
  """
  # Create our custom estimator using our model function
  estimator = tf.estimator.Estimator(
      model_fn=anomaly_detection,
      model_dir=args["output_dir"],
      params={key: val for key, val in args.items()})

  if args["training_mode"] == "reconstruction":
    if args["model_type"] == "pca":
      estimator.train(
          input_fn=read_dataset(
              filename=args["train_file_pattern"],
              mode=tf.estimator.ModeKeys.EVAL,
              batch_size=args["train_batch_size"],
              params=args),
          steps=None)
    else:  # dense_autoencoder or lstm_enc_dec_autoencoder
      # Create early stopping hook to help reduce overfitting
      early_stopping_hook = tf.contrib.estimator.stop_if_no_decrease_hook(
          estimator=estimator,
          metric_name="rmse",
          max_steps_without_decrease=100,
          min_steps=1000,
          run_every_secs=60,
          run_every_steps=None)

      # Create train spec to read in our training data
      train_spec = tf.estimator.TrainSpec(
          input_fn=read_dataset(
              filename=args["train_file_pattern"],
              mode=tf.estimator.ModeKeys.TRAIN,
              batch_size=args["train_batch_size"],
              params=args),
          max_steps=args["train_steps"],
          hooks=[early_stopping_hook])

      # Create eval spec to read in our validation data and export our model
      eval_spec = tf.estimator.EvalSpec(
          input_fn=read_dataset(
              filename=args["eval_file_pattern"],
              mode=tf.estimator.ModeKeys.EVAL,
              batch_size=args["eval_batch_size"],
              params=args),
          steps=None,
          start_delay_secs=args["start_delay_secs"],  # start eval after N secs
          throttle_secs=args["throttle_secs"])  # evaluate every N secs

      # Create train and evaluate loop to train and evaluate our estimator
      tf.estimator.train_and_evaluate(
          estimator=estimator, train_spec=train_spec, eval_spec=eval_spec)
  else:
    # if args["training_mode"] == "calculate_error_distribution_statistics"
    # Get final mahalanobis statistics over the entire val_1 dataset

    # if args["training_mode"] == "tune_anomaly_thresholds"
    # Tune anomaly thresholds using val_2 and val_anom datasets
    train_spec = tf.estimator.TrainSpec(
        input_fn=read_dataset(
            filename=args["train_file_pattern"],
            mode=tf.estimator.ModeKeys.EVAL,  # read through val data once
            batch_size=args["train_batch_size"],
            params=args),
        max_steps=args["train_steps"])

    if args["training_mode"] == "calculate_error_distribution_statistics":
      # Evaluate until the end of eval files
      eval_steps = None
        
      # Don't create exporter for serving yet since anomaly thresholds
      # aren't trained yet
      exporter = None
    elif args["training_mode"] == "tune_anomaly_thresholds":
      if args["labeled_tune_thresh"]:
        # Evaluate until the end of eval files
        eval_steps = None
      else:
        # Don't evaluate
        eval_steps = 0
        
      # Create exporter that uses serving_input_fn to create saved_model
      # for serving
      exporter = tf.estimator.LatestExporter(
          name="exporter",
          serving_input_receiver_fn=lambda: serving_input_fn(args["seq_len"]))
    else:
      print("{0} isn't a valid training mode!".format(args["training_mode"]))

    # Create eval spec to read in our validation data and export our model
    eval_spec = tf.estimator.EvalSpec(
        input_fn=read_dataset(
            filename=args["eval_file_pattern"],
            mode=tf.estimator.ModeKeys.EVAL,
            batch_size=args["eval_batch_size"],
            params=args),
        steps=eval_steps,
        exporters=exporter,
        start_delay_secs=args["start_delay_secs"],  # start eval after N secs
        throttle_secs=args["throttle_secs"])  # evaluate every N secs

  if (args["training_mode"] == "calculate_error_distribution_statistics" or 
      args["training_mode"] == "tune_anomaly_thresholds"):
    # Create train and evaluate loop to train and evaluate our estimator
    tf.estimator.train_and_evaluate(
        estimator=estimator, train_spec=train_spec, eval_spec=eval_spec)
