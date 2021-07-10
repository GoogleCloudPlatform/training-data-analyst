import tensorflow as tf

# Set logging to be level of INFO
tf.logging.set_verbosity(tf.logging.INFO)

# Determine CSV and label columns
CSV_COLUMNS = ["med_sales_price_agg", "labels_agg"]
LABEL_COLUMN = "labels_agg"

# Set default values for each CSV column
DEFAULTS = [[""] for _ in CSV_COLUMNS[:-1]] + [[0.0]]


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
        input=string_tensor, axis=0), delimiter=";")

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


def decode_csv(value_column, seq_len):
    """Decodes CSV file into tensors.

    Given single string tensor and sequence length, returns features dictionary
    of tensors and labels tensor.

    Args:
        value_column: tf.string tensor of shape () compromising entire line of
            CSV file.
        seq_len: Number of timesteps in sequence.

    Returns:
        Features dictionary of tensors and labels tensor.
    """
    columns = tf.decode_csv(
        records=value_column,
        record_defaults=DEFAULTS,
        field_delim=",")

    features = dict(zip(CSV_COLUMNS, columns))

    labels = tf.cast(x=features.pop(LABEL_COLUMN), dtype=tf.float64)

    features = convert_sequences_from_strings_to_floats(
        features=features,
        column_list=CSV_COLUMNS[:-1],
        seq_len=seq_len)

    return features, labels


def read_dataset(filename, mode, batch_size, seq_len):
    """Reads CSV time series dataset using tf.data, doing necessary preprocessing.

    Given filename, mode, batch size and other parameters, read CSV dataset using
    Dataset API, apply necessary preprocessing, and return an input function to
    the Estimator API.

    Args:
        filename: The file pattern that we want to read into our tf.data dataset.
        mode: The estimator ModeKeys. Can be TRAIN or EVAL.
        batch_size: Number of examples to read and combine into a single tensor.
        seq_len: Number of timesteps for each example.

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
        dataset = tf.data.TextLineDataset(filenames=file_list).skip(count=1)  # Read text file

        # Decode the CSV file into a features dictionary of tensors
        dataset = dataset.map(
            map_func=lambda x: decode_csv(
                value_column=x,
                seq_len=seq_len))

        # Determine amount of times to repeat file if we are training or evaluating
        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None    # indefinitely
        else:
            num_epochs = 1    # end-of-input after this

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


def create_LSTM_stack(lstm_hidden_units):
  """Create LSTM stacked cells.

  Given list of LSTM hidden units return `MultiRNNCell`.

  Args:
    lstm_hidden_units: List of integers for the number of hidden units in each
      layer.

  Returns:
    `MultiRNNCell` object of stacked LSTM layers.
  """
  # First create a list of LSTM cell objects using our list of lstm hidden
  # unit sizes
  lstm_cells = [tf.contrib.rnn.BasicLSTMCell(
      num_units=units,
      forget_bias=1.0,
      state_is_tuple=True)
                for units in lstm_hidden_units]

  # Create a stack of layers of LSTM cells
  # Combines list into MultiRNNCell object
  stacked_lstm_cells = tf.contrib.rnn.MultiRNNCell(
      cells=lstm_cells,
      state_is_tuple=True)

  return stacked_lstm_cells


# Create our model function to be used in our custom estimator
def sequence_to_one_model(features, labels, mode, params):
    """Custom Estimator model function for sequence to one.

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
    # Get input sequence tensor into correct shape

    # Stack all of the features into a 3-D tensor
    X = tf.stack(values=[features[key] for key in CSV_COLUMNS[:-1]], axis=2)
    
    # Unstack 3-D features tensor into a sequence(list) of 2-D tensors
    X_sequence = tf.unstack(value=X, num=params["seq_len"], axis=1)

    # 1. Configure the RNN
    stacked_lstm_cells = create_LSTM_stack(params["lstm_hidden_units"])
    
    lstm_cell = tf.compat.v1.nn.rnn_cell.LSTMCell(
        num_units=params["lstm_hidden_units"], forget_bias=1.0)
    outputs, _ = tf.compat.v1.nn.static_rnn(
        cell=stacked_lstm_cells, inputs=X_sequence, dtype=tf.float64)
    
    # Slice to keep only the last cell of the RNN
    output = outputs[-1]
    
    # Output is result of linear activation of last layer of RNN
    predictions = tf.layers.dense(inputs=output, units=1, activation=None)
        
    # 2. Loss function, training/eval ops
    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
        labels = tf.expand_dims(input=labels, axis=-1)

        loss = tf.losses.mean_squared_error(labels=labels, predictions=predictions)
        train_op = tf.contrib.layers.optimize_loss(
            loss=loss,
            global_step=tf.train.get_global_step(),
            learning_rate=params["learning_rate"],
            optimizer="SGD")
        eval_metric_ops = {
            "rmse": tf.metrics.root_mean_squared_error(labels=labels, predictions=predictions)
        }
    else:
        loss = None
        train_op = None
        eval_metric_ops = None
    
    # 3. Create predictions
    predictions_dict = {"predicted": predictions}
    
    # 4. Create export outputs
    export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs=predictions)}
    
    # 5. Return EstimatorSpec
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
            source=[placeholder[x]], delimiter=";").values,
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
        for feature in CSV_COLUMNS[:-1]
    }

    # Create feature tensors
    features = {key: fix_shape_and_type_for_serving(placeholder=tensor)
                for key, tensor in feature_placeholders.items()}

    # Fix dynamic shape ambiguity of feature tensors for our dense layers
    features = {key: get_shape_and_set_modified_shape_2D(
        tensor=tensor, additional_dimension_sizes=[seq_len])
                for key, tensor in features.items()}

    return tf.estimator.export.ServingInputReceiver(
            features=features, receiver_tensors=feature_placeholders)


# Create custom estimator's train and evaluate function
def train_and_evaluate(args):
    estimator = tf.estimator.Estimator(
        model_fn = sequence_to_one_model,
        model_dir = args["output_dir"],
        params={"seq_len": args["seq_len"],
                "lstm_hidden_units": args["lstm_hidden_units"],
                "learning_rate": args["learning_rate"]})

    train_spec = tf.estimator.TrainSpec(
        input_fn = read_dataset(
            filename=args["train_file_pattern"],
            mode=tf.estimator.ModeKeys.TRAIN,
            batch_size=args["train_batch_size"],
            seq_len=args["seq_len"]),
        max_steps = args["train_steps"])

    exporter = tf.estimator.LatestExporter(
        name="exporter",
        serving_input_receiver_fn=lambda: serving_input_fn(args["seq_len"]))

    eval_spec = tf.estimator.EvalSpec(
        input_fn = read_dataset(
            filename=args["eval_file_pattern"],
            mode=tf.estimator.ModeKeys.EVAL,
            batch_size=args["eval_batch_size"],
            seq_len=args["seq_len"]),
        steps = None,
        exporters = exporter,
        start_delay_secs=args["start_delay_secs"],
        throttle_secs=args["throttle_secs"])

    tf.estimator.train_and_evaluate(
        estimator=estimator,
        train_spec=train_spec,
        eval_spec=eval_spec)