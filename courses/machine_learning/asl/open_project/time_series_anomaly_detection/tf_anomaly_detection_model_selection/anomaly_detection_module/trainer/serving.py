import tensorflow as tf


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


def serving_input_fn(feat_names, seq_len):
  """Serving input function.

  Given the sequence length, return ServingInputReceiver object.

  Args:
    feat_names: List of string names of features.
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
      for feature in feat_names
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
