import tensorflow as tf
from .globals import *


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
        field_delim=",")

    features = dict(zip(UNLABELED_CSV_COLUMNS, columns))
    features = convert_sequences_from_strings_to_floats(
        features=features,
        column_list=UNLABELED_CSV_COLUMNS,
        seq_len=seq_len)
    return features
  else:
    # For subset of CSV files that DO have labels
    columns = tf.decode_csv(
        records=value_column,
        record_defaults=LABELED_DEFAULTS,
        field_delim=",")

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
            training_mode=params["training_mode"],
            labeled_tune_thresh=params["labeled_tune_thresh"]))

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
