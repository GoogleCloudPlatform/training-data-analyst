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
    def decode_csv(value_column, seq_len):
      def convert_sequences_from_strings_to_floats(features, column_list):
        def split_and_convert_string(string_tensor):
          # Split string tensor into a sparse tensor based on delimiter
          split_string = tf.string_split(source = tf.expand_dims(
            input = string_tensor, axis = 0), delimiter = ",")

          # Converts the values of the sparse tensor to floats
          converted_tensor = tf.string_to_number(
            string_tensor = split_string.values, 
            out_type = tf.float64)

          # Create a new sparse tensor with the new converted values, 
          # because the original sparse tensor values are immutable
          new_sparse_tensor = tf.SparseTensor(
            indices = split_string.indices, 
            values = converted_tensor, 
            dense_shape = split_string.dense_shape)

          # Create a dense tensor of the float values that were converted from text csv
          dense_floats = tf.sparse_tensor_to_dense(
            sp_input = new_sparse_tensor, default_value = 0.0)

          dense_floats_vector = tf.squeeze(input = dense_floats, axis = 0)

          return dense_floats_vector
          
        for column in column_list:
          features[column] = split_and_convert_string(features[column])
          features[column].set_shape([seq_len])

        return features
        
      if mode == tf.estimator.ModeKeys.TRAIN or (mode == tf.estimator.ModeKeys.EVAL and params["evaluation_mode"] != "tune_anomaly_thresholds"):
        columns = tf.decode_csv(
          records = value_column, 
          record_defaults = UNLABELED_DEFAULTS, 
          field_delim = ";")
        features = dict(zip(UNLABELED_CSV_COLUMNS, columns))
        features = convert_sequences_from_strings_to_floats(
          features, UNLABELED_CSV_COLUMNS)
        return features
      else:
        columns = tf.decode_csv(
          records = value_column, 
          record_defaults = LABELED_DEFAULTS, 
          field_delim = ";")
        features = dict(zip(LABELED_CSV_COLUMNS, columns))
        labels = tf.cast(x = features.pop(LABEL_COLUMN), dtype = tf.float64)
        features = convert_sequences_from_strings_to_floats(
          features, LABELED_CSV_COLUMNS[0:-1])
        return features, labels
    
    # Create list of files that match pattern
    file_list = tf.gfile.Glob(filename = filename)

    # Create dataset from file list
    dataset = tf.data.TextLineDataset(filenames = file_list)  # Read text file

    # Decode the CSV file into a features dictionary of tensors
    dataset = dataset.map(map_func = lambda x: decode_csv(x, params["seq_len"]))
    
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

# This function updates the count of records used
def update_count(count_a, count_b):
  return count_a + count_b

# This function updates the mahalanobis distance variables when number_of_rows equals 1
def singleton_batch_cov_variable_updating(
  inner_size, 
  X, 
  count_variable, 
  mean_variable, 
  cov_variable, 
  eps):
  # This function updates the mean vector incrementally
  def update_mean_incremental(count_a, mean_a, value_b):
    mean_ab = (mean_a * tf.cast(x = count_a, dtype = tf.float64) + \
           tf.squeeze(input = value_b, axis = 0)) / tf.cast(x = count_a + 1, dtype = tf.float64)
    return mean_ab

  # This function updates the covariance matrix incrementally
  def update_cov_incremental(count_a, mean_a, cov_a, value_b, mean_ab, sample_cov):
    if sample_cov == True:
      cov_ab = (cov_a * tf.cast(x = count_a - 1, dtype = tf.float64) + \
            tf.matmul(a = value_b - mean_a, b = value_b - mean_ab, transpose_a = True)) \
        / tf.cast(x = count_a, dtype = tf.float64)
    else:
      cov_ab = (cov_a * tf.cast(x = count_a, dtype = tf.float64) + \
            tf.matmul(a = value_b - mean_a, b = value_b - mean_ab, transpose_a = True)) \
        / tf.cast(x = count_a + 1, dtype = tf.float64)
    return cov_ab

  # Calculate new combined mean to use for incremental covariance matrix calculation
  mean_ab = update_mean_incremental(
    count_a = count_variable, 
    mean_a = mean_variable, 
    value_b = X) # time_shape = (num_features,), features_shape = (sequence_length,)

  # Update running variables from single example
  count_tensor = update_count(
    count_a = count_variable, 
    count_b = 1) # time_shape = (), features_shape = ()

  mean_tensor = mean_ab # time_shape = (num_features,), features_shape = (sequence_length,)

  if inner_size == 1:
    cov_tensor = tf.zeros_like(
      tensor = cov_variable, dtype = tf.float64)
  else:
    # time_shape = (num_features, num_features)
    # features_shape = (sequence_length, sequence_length)
    cov_tensor = update_cov_incremental(
      count_a = count_variable, 
      mean_a = mean_variable, 
      cov_a = cov_variable, 
      value_b = X, 
      mean_ab = mean_ab, 
      sample_cov = True)

  # Assign values to variables, use control dependencies around return to enforce the mahalanobis 
  # variables to be assigned, the control order matters, hence the separate contexts
  with tf.control_dependencies(
    control_inputs = [tf.assign(
      ref = cov_variable, 
      value = cov_tensor)]):
    with tf.control_dependencies(
      control_inputs = [tf.assign(
        ref = mean_variable, 
        value = mean_tensor)]):
      with tf.control_dependencies(
        control_inputs = [tf.assign(
          ref = count_variable, 
          value = count_tensor)]):
        return tf.identity(input = cov_variable), tf.identity(input = mean_variable), tf.identity(input = count_variable)

# This function updates the mahalanobis distance variables when number_of_rows does NOT equal 1
def non_singleton_batch_cov_variable_updating(
  cur_batch_size, 
  inner_size, 
  X, 
  count_variable, 
  mean_variable, 
  cov_variable, 
  eps):
  # This function updates the mean vector using a batch of data
  def update_mean_batch(count_a, mean_a, count_b, mean_b):
    mean_ab = (mean_a * tf.cast(x = count_a, dtype = tf.float64) + \
               mean_b * tf.cast(x = count_b, dtype = tf.float64)) \
               / tf.cast(x = count_a + count_b, dtype = tf.float64)
    return mean_ab

  # This function updates the covariance matrix using a batch of data
  def update_cov_batch(count_a, mean_a, cov_a, count_b, mean_b, cov_b, sample_cov):
    mean_diff = tf.expand_dims(input = mean_a - mean_b, axis = 0)

    if sample_cov == True:
      cov_ab = (cov_a * tf.cast(x = count_a - 1, dtype = tf.float64) + \
                cov_b * tf.cast(x = count_b - 1, dtype = tf.float64) + \
                tf.matmul(a = mean_diff, b = mean_diff, transpose_a = True) * \
                tf.cast(x = count_a * count_b, dtype = tf.float64) \
                / tf.cast(x = count_a + count_b, dtype = tf.float64)) \
                / tf.cast(x = count_a + count_b - 1, dtype = tf.float64)
    else:
      cov_ab = (cov_a * tf.cast(x = count_a, dtype = tf.float64) + \
                cov_b * tf.cast(x = count_b, dtype = tf.float64) + \
                tf.matmul(a = mean_diff, b = mean_diff, transpose_a = True) * \
                tf.cast(x = count_a * count_b, dtype = tf.float64) \
                / tf.cast(x = count_a + count_b, dtype = tf.float64)) \
                / tf.cast(x = count_a + count_b, dtype = tf.float64)
    return cov_ab          

  # Find statistics of batch
  number_of_rows = cur_batch_size * inner_size

  # time_shape = (num_features,), features_shape = (sequence_length,)
  X_mean = tf.reduce_mean(input_tensor = X, axis = 0)

  # time_shape = (cur_batch_size * sequence_length, num_features)
  # features_shape = (cur_batch_size * num_features, sequence_length)
  X_centered = X - X_mean

  if inner_size > 1:
    # time_shape = (num_features, num_features)
    # features_shape = (sequence_length, sequence_length)
    X_cov = tf.matmul(
      a = X_centered,
      b = X_centered, 
      transpose_a = True) / tf.cast(x = number_of_rows - 1, dtype = tf.float64)

  # Update running variables from batch statistics
  count_tensor = update_count(
    count_a = count_variable, 
    count_b = number_of_rows) # time_shape = (), features_shape = ()

  mean_tensor = update_mean_batch(
    count_a = count_variable, 
    mean_a = mean_variable, 
    count_b = number_of_rows, 
    mean_b = X_mean) # time_shape = (num_features,), features_shape = (sequence_length,)

  if inner_size == 1:
    cov_tensor = tf.zeros_like(
      tensor = cov_variable, dtype = tf.float64)
  else:
    # time_shape = (num_features, num_features)
    # features_shape = (sequence_length, sequence_length)
    cov_tensor = update_cov_batch(
      count_a = count_variable, 
      mean_a = mean_variable, 
      cov_a = cov_variable, 
      count_b = number_of_rows, 
      mean_b = X_mean, 
      cov_b = X_cov, 
      sample_cov = True)

  # Assign values to variables, use control dependencies around return to enforce the mahalanobis 
  # variables to be assigned, the control order matters, hence the separate contexts
  with tf.control_dependencies(
    control_inputs = [tf.assign(ref = cov_variable, value = cov_tensor)]):
    with tf.control_dependencies(
      control_inputs = [tf.assign(ref = mean_variable, value = mean_tensor)]):
      with tf.control_dependencies(
        control_inputs = [tf.assign(ref = count_variable, value = count_tensor)]):
        return tf.identity(input = cov_variable), tf.identity(input = mean_variable), tf.identity(input = count_variable)

def mahalanobis_distance(error_vectors_reshaped, mean_vector, inv_covariance, final_shape):
  # time_shape = (current_batch_size * seq_len, num_features)
  # features_shape = (current_batch_size * num_features, seq_len)
  error_vectors_reshaped_centered = error_vectors_reshaped - mean_vector

  # time_shape = (num_features, current_batch_size * seq_len)
  # features_shape = (seq_len, current_batch_size * num_features)
  mahalanobis_right_product = tf.matmul(
    a = inv_covariance,
    b = error_vectors_reshaped_centered,
    transpose_b = True)

  # time_shape = (current_batch_size * seq_len, current_batch_size * seq_len)
  # features_shape = (current_batch_size * num_features, current_batch_size * num_features)
  mahalanobis_distance_vectorized = tf.matmul(
    a = error_vectors_reshaped_centered,
    b = mahalanobis_right_product)

  # time_shape = (current_batch_size * seq_len,)
  # features_shape = (current_batch_size * num_features,)
  mahalanobis_distance_flat = tf.diag_part(input = mahalanobis_distance_vectorized)

  # time_shape = (current_batch_size, seq_len)
  # features_shape = (current_batch_size, num_features)
  mahalanobis_distance_final_shaped = tf.reshape(
    tensor = mahalanobis_distance_flat, 
    shape = [-1, final_shape])

  # time_shape = (current_batch_size, seq_len)
  # features_shape = (current_batch_size, num_features)
  mahalanobis_distance_final_shaped_abs = tf.abs(x = mahalanobis_distance_final_shaped)

  return mahalanobis_distance_final_shaped_abs

def update_anomaly_threshold_variables(
  labels_normal_mask, 
  labels_anomalous_mask, 
  num_thresholds, 
  anomaly_thresholds, 
  mahalanobis_distance, 
  tp_at_thresholds_variable, 
  fn_at_thresholds_variable, 
  fp_at_thresholds_variable, 
  tn_at_thresholds_variable,
  mode):
  
  if mode == tf.estimator.ModeKeys.TRAIN:
    # time_shape = (num_time_anomaly_thresholds, current_batch_size, sequence_length)
    # features_shape = (num_features_anomaly_thresholds, current_batch_size, number_of_features)
    mahalanobis_distance_over_thresholds = tf.map_fn(
      fn = lambda anomaly_threshold: mahalanobis_distance > anomaly_threshold, 
      elems = anomaly_thresholds, 
      dtype = tf.bool)
  else:
    # time_shape = (current_batch_size, sequence_length)
    # features_shape = (current_batch_size, number_of_features)
    mahalanobis_distance_over_thresholds = mahalanobis_distance > anomaly_thresholds

  # time_shape = (num_time_anomaly_thresholds, current_batch_size)
  # features_shape = (num_features_anomaly_thresholds, current_batch_size)    
  mahalanobis_distance_any_over_thresholds = tf.reduce_any(
    input_tensor = mahalanobis_distance_over_thresholds, 
    axis = -1)
    
  if mode == tf.estimator.ModeKeys.EVAL:
    # time_shape = (1, current_batch_size)
    # features_shape = (1, current_batch_size)
    mahalanobis_distance_any_over_thresholds = tf.expand_dims(
      input = mahalanobis_distance_any_over_thresholds, axis = 0)

  # time_shape = (num_time_anomaly_thresholds, current_batch_size)
  # features_shape = (num_features_anomaly_thresholds, current_batch_size)
  predicted_normals = tf.equal(
    x = mahalanobis_distance_any_over_thresholds, 
    y = False)

  # time_shape = (num_time_anomaly_thresholds, current_batch_size)
  # features_shape = (num_features_anomaly_thresholds, current_batch_size)
  predicted_anomalies = tf.equal(
    x = mahalanobis_distance_any_over_thresholds, 
    y = True)
  
  # Calculate confusion matrix of current batch
  # time_shape = (num_time_anomaly_thresholds,)
  # features_shape = (num_features_anomaly_thresholds,)
  tp = tf.reduce_sum(
    input_tensor = tf.cast(
      x = tf.map_fn(
        fn = lambda threshold: tf.logical_and(
          x = labels_anomalous_mask, 
          y = predicted_anomalies[threshold, :]), 
        elems = tf.range(start = 0, limit = num_thresholds, dtype = tf.int64), 
        dtype = tf.bool), 
      dtype = tf.int64), 
    axis = 1)

  fn = tf.reduce_sum(
    input_tensor = tf.cast(
      x = tf.map_fn(
        fn = lambda threshold: tf.logical_and(
          x = labels_anomalous_mask, 
          y = predicted_normals[threshold, :]), 
        elems = tf.range(start = 0, limit = num_thresholds, dtype = tf.int64), 
        dtype = tf.bool), 
      dtype = tf.int64), 
    axis = 1)

  fp = tf.reduce_sum(
    input_tensor = tf.cast(
      x = tf.map_fn(
        fn = lambda threshold: tf.logical_and(
          x = labels_normal_mask, 
          y = predicted_anomalies[threshold, :]), 
        elems = tf.range(start = 0, limit = num_thresholds, dtype = tf.int64), 
        dtype = tf.bool), 
      dtype = tf.int64), 
    axis = 1)

  tn = tf.reduce_sum(
    input_tensor = tf.cast(
      x = tf.map_fn(
        fn = lambda threshold: tf.logical_and(
          x = labels_normal_mask, 
          y = predicted_normals[threshold, :]), 
        elems = tf.range(start = 0, limit = num_thresholds, dtype = tf.int64), 
        dtype = tf.bool), 
      dtype = tf.int64), 
    axis = 1)
  
  if mode == tf.estimator.ModeKeys.EVAL:
    # shape = ()
    tp = tf.squeeze(input = tp)
    fn = tf.squeeze(input = fn)
    fp = tf.squeeze(input = fp)
    tn = tf.squeeze(input = tn)

  with tf.control_dependencies(
    control_inputs = [tf.assign_add(ref = tp_at_thresholds_variable, value = tp), 
                      tf.assign_add(ref = fn_at_thresholds_variable, value = fn), 
                      tf.assign_add(ref = fp_at_thresholds_variable, value = fp), 
                      tf.assign_add(ref = tn_at_thresholds_variable, value = tn)]):
    return tf.identity(input = tp_at_thresholds_variable), tf.identity(input = fn_at_thresholds_variable), tf.identity(input = fp_at_thresholds_variable), tf.identity(input = tn_at_thresholds_variable)

def calculate_composite_classification_metrics(anomaly_thresholds, tp, fn, fp, tn, f_score_beta):
  # time_shape = (num_time_anomaly_thresholds,)
  # features_shape = (num_features_anomaly_thresholds,)
  acc = tf.cast(x = tp + tn, dtype = tf.float64) \
    / tf.cast(x = tp + fn + fp + tn, dtype = tf.float64)
  pre = tf.cast(x = tp, dtype = tf.float64) / tf.cast(x = tp + fp, dtype = tf.float64)
  rec = tf.cast(x = tp, dtype = tf.float64) / tf.cast(x = tp + fn, dtype = tf.float64)
  f_beta_score = (1.0 + f_score_beta ** 2) * (pre * rec) / (f_score_beta ** 2 * pre + rec)

  return acc, pre, rec, f_beta_score

def find_best_anomaly_threshold(
  anomaly_thresholds, f_beta_score, user_passed_anomaly_threshold, anomaly_threshold_variable):
  if user_passed_anomaly_threshold == None:
    best_anomaly_threshold = tf.gather(
      params = anomaly_thresholds, 
      indices = tf.argmax(input = f_beta_score, 
      axis = 0)) # shape = ()
  else:
    best_anomaly_threshold = user_passed_anomaly_threshold # shape = ()

  with tf.control_dependencies(
    control_inputs = [
      tf.assign(ref = anomaly_threshold_variable, value = best_anomaly_threshold)]):
    return tf.identity(input = anomaly_threshold_variable)

# Create our model function to be used in our custom estimator
def pca_anomaly_detection(features, labels, mode, params):
  print("\npca_anomaly_detection: features = \n{}".format(features))
  print("pca_anomaly_detection: labels = \n{}".format(labels))
  print("pca_anomaly_detection: mode = \n{}".format(mode))
  print("pca_anomaly_detection: params = \n{}".format(params))

  # 0. Get input sequence tensor into correct shape
  # Get dynamic batch size in case there was a partially filled batch
  cur_batch_size = tf.shape(
    input = features[UNLABELED_CSV_COLUMNS[0]], out_type = tf.int64)[0]

  # Get the number of features 
  num_features = len(UNLABELED_CSV_COLUMNS)

  # Stack all of the features into a 3-D tensor
  X = tf.stack(
    values = [features[key] for key in UNLABELED_CSV_COLUMNS], 
    axis = 2) # shape = (cur_batch_size, seq_len, num_features)

  # Reshape into a 2-D tensors
  # Time based
  # shape = (cur_batch_size * seq_len, num_features)
  X_time = tf.reshape(
    tensor = X, 
    shape = [cur_batch_size * params["seq_len"], num_features])
  
  # Features based
  # shape = (cur_batch_size, num_features, seq_len)
  X_transposed = tf.transpose(a = X, perm = [0, 2, 1])
  # shape = (cur_batch_size * num_features, seq_len)
  X_features = tf.reshape(
    tensor = X_transposed, 
    shape = [cur_batch_size * num_features, params["seq_len"]])

  ################################################################################
  
  # Variables for calculating error distribution statistics
  with tf.variable_scope(name_or_scope = "pca_variables", reuse = tf.AUTO_REUSE):
    # Time based
    pca_time_count_variable = tf.get_variable(
      name = "pca_time_count_variable", # shape = ()
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False)

    pca_time_mean_variable = tf.get_variable(
      name = "pca_time_mean_variable", # shape = (num_features,)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [num_features],  dtype = tf.float64),
      trainable = False)

    pca_time_cov_variable = tf.get_variable(
      name = "pca_time_cov_variable", # shape = (num_features, num_features)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [num_features, num_features], dtype = tf.float64),
      trainable = False)

    pca_time_eigenvalues_variable = tf.get_variable(
      name = "pca_time_eigenvalues_variable", # shape = (num_features,)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [num_features], dtype = tf.float64),
      trainable = False)

    pca_time_eigenvectors_variable = tf.get_variable(
      name = "pca_time_eigenvectors_variable", # shape = (num_features, num_features)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [num_features, num_features], dtype = tf.float64),
      trainable = False)

    # Features based
    pca_features_count_variable = tf.get_variable(
      name = "pca_features_count_variable", # shape = ()
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False)

    pca_features_mean_variable = tf.get_variable(
      name = "pca_features_mean_variable", # shape = (seq_len,)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [params["seq_len"]], dtype = tf.float64),
      trainable = False)

    pca_features_cov_variable = tf.get_variable(
      name = "pca_features_cov_variable", # shape = (seq_len, seq_len)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [params["seq_len"], params["seq_len"]], dtype = tf.float64),
      trainable = False)

    pca_features_eigenvalues_variable = tf.get_variable(
      name = "pca_features_eigenvalues_variable", # shape = (seq_len,)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [params["seq_len"]], dtype = tf.float64),
      trainable = False)

    pca_features_eigenvectors_variable = tf.get_variable(
      name = "pca_features_eigenvectors_variable", # shape = (seq_len, seq_len)
      dtype = tf.float64,
      initializer = tf.zeros(shape = [params["seq_len"], params["seq_len"]], dtype = tf.float64),
      trainable = False)
  
  # Variables for calculating error distribution statistics
  with tf.variable_scope(
    name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
    # Time based
    abs_err_count_time_variable = tf.get_variable(
      name = "abs_err_count_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    abs_err_mean_time_variable = tf.get_variable(
      name = "abs_err_mean_time_variable",
      dtype = tf.float64,
      initializer = tf.zeros(shape = [num_features], dtype = tf.float64),
      trainable = False) # shape = (num_features,)

    abs_err_cov_time_variable = tf.get_variable(
      name = "abs_err_cov_time_variable",
      dtype = tf.float64,
      initializer = tf.zeros(shape = [num_features, num_features], dtype = tf.float64),
      trainable = False) # shape = (num_features, num_features)

    abs_err_inv_cov_time_variable = tf.get_variable(
      name = "abs_err_inv_cov_time_variable",
      dtype = tf.float64,
      initializer = tf.zeros(shape = [num_features, num_features], dtype = tf.float64),
      trainable = False) # shape = (num_features, num_features)

    # Features based
    abs_err_count_features_variable = tf.get_variable(
      name = "abs_err_count_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    abs_err_mean_features_variable = tf.get_variable(
      name = "abs_err_mean_features_variable",
      dtype = tf.float64,
      initializer = tf.zeros(shape = [params["seq_len"]], dtype = tf.float64),
      trainable = False) # shape = (seq_len,)

    abs_err_cov_features_variable = tf.get_variable(
      name = "abs_err_cov_features_variable",
      dtype = tf.float64,
      initializer = tf.zeros(shape = [params["seq_len"], params["seq_len"]], dtype = tf.float64),
      trainable = False) # shape = (seq_len, seq_len)

    abs_err_inv_cov_features_variable = tf.get_variable(
      name = "abs_err_inv_cov_features_variable",
      dtype = tf.float64,
      initializer = tf.zeros(shape = [params["seq_len"], params["seq_len"]], dtype = tf.float64),
      trainable = False) # shape = (seq_len, seq_len)
  
  # Variables for automatically tuning anomaly thresholds
  with tf.variable_scope(
    name_or_scope = "mahalanobis_distance_threshold_variables", reuse = tf.AUTO_REUSE):
    # Time based
    tp_at_thresholds_time_variable = tf.get_variable(
      name = "tp_at_thresholds_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_time_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_time_anomaly_thresholds,)

    fn_at_thresholds_time_variable = tf.get_variable(
      name = "fn_at_thresholds_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_time_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_time_anomaly_thresholds,)

    fp_at_thresholds_time_variable = tf.get_variable(
      name = "fp_at_thresholds_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_time_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_time_anomaly_thresholds,)

    tn_at_thresholds_time_variable = tf.get_variable(
      name = "tn_at_thresholds_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_time_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_time_anomaly_thresholds,)

    time_anomaly_threshold_variable = tf.get_variable(
      name = "time_anomaly_threshold_variable",
      dtype = tf.float64,
      initializer = tf.zeros(shape = [], dtype = tf.float64),
      trainable = False) # shape = ()

    # Features based
    tp_at_thresholds_features_variable = tf.get_variable(
      name = "tp_at_thresholds_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_features_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_features_anomaly_thresholds,)

    fn_at_thresholds_features_variable = tf.get_variable(
      name = "fn_at_thresholds_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_features_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_features_anomaly_thresholds,)

    fp_at_thresholds_features_variable = tf.get_variable(
      name = "fp_at_thresholds_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_features_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_features_anomaly_thresholds,)

    tn_at_thresholds_features_variable = tf.get_variable(
      name = "tn_at_thresholds_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [params["num_features_anomaly_thresholds"]], dtype = tf.int64),
      trainable = False) # shape = (num_features_anomaly_thresholds,)

    features_anomaly_threshold_variable = tf.get_variable(
      name = "features_anomaly_threshold_variable", # shape = ()
      dtype = tf.float64,
      initializer = tf.zeros(shape = [], dtype = tf.float64),
      trainable = False)

  # Variables for automatically tuning anomaly thresholds
  with tf.variable_scope(
    name_or_scope = "anomaly_threshold_eval_variables", reuse = tf.AUTO_REUSE):
    # Time based
    tp_at_threshold_eval_time_variable = tf.get_variable(
      name = "tp_at_threshold_eval_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    fn_at_threshold_eval_time_variable = tf.get_variable(
      name = "fn_at_threshold_eval_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    fp_at_threshold_eval_time_variable = tf.get_variable(
      name = "fp_at_threshold_eval_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    tn_at_threshold_eval_time_variable = tf.get_variable(
      name = "tn_at_threshold_eval_time_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    # Features based
    tp_at_threshold_eval_features_variable = tf.get_variable(
      name = "tp_at_threshold_eval_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    fn_at_threshold_eval_features_variable = tf.get_variable(
      name = "fn_at_threshold_eval_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    fp_at_threshold_eval_features_variable = tf.get_variable(
      name = "fp_at_threshold_eval_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

    tn_at_threshold_eval_features_variable = tf.get_variable(
      name = "tn_at_threshold_eval_features_variable",
      dtype = tf.int64,
      initializer = tf.zeros(shape = [], dtype = tf.int64),
      trainable = False) # shape = ()

  dummy_variable = tf.get_variable(
    name = "dummy_variable",
    dtype = tf.float64,
    initializer = tf.zeros(shape = [], dtype = tf.float64),
    trainable = True) # shape = ()
  
  # Now branch off based on which mode we are in
  predictions_dict = None
  loss = None
  train_op = None
  eval_metric_ops = None
  export_outputs = None
  
  # 3. Loss function, training/eval ops
  if mode == tf.estimator.ModeKeys.TRAIN and params["evaluation_mode"] == "reconstruction":
    with tf.variable_scope(name_or_scope = "pca_variables", reuse = tf.AUTO_REUSE):
      # Check if batch is a singleton or not, very important for covariance math

      # Time based ########################################
      singleton_condition = tf.equal(
        x = cur_batch_size * params["seq_len"], y = 1) # shape = ()

      pca_time_cov_variable, pca_time_mean_variable, pca_time_count_variable = tf.cond(
        pred = singleton_condition, 
        true_fn = lambda: singleton_batch_cov_variable_updating(
          params["seq_len"], 
          X_time, 
          pca_time_count_variable, 
          pca_time_mean_variable, 
          pca_time_cov_variable,
          params["eps"]), 
        false_fn = lambda: non_singleton_batch_cov_variable_updating(
          cur_batch_size, 
          params["seq_len"], 
          X_time, 
          pca_time_count_variable, 
          pca_time_mean_variable, 
          pca_time_cov_variable,
          params["eps"]))

      pca_time_eigenvalues_tensor, pca_time_eigenvectors_tensor = tf.linalg.eigh(
        tensor = pca_time_cov_variable) # shape = (num_features,) & (num_features, num_features)

      # Features based ########################################
      singleton_features_condition = tf.equal(
        x = cur_batch_size * num_features, y = 1) # shape = ()

      pca_features_cov_variable, pca_features_mean_variable, pca_features_count_variable = tf.cond(
        pred = singleton_features_condition, 
        true_fn = lambda: singleton_batch_cov_variable_updating(
          num_features, 
          X_features, 
          pca_features_count_variable, pca_features_mean_variable, 
          pca_features_cov_variable,
          params["eps"]), 
        false_fn = lambda: non_singleton_batch_cov_variable_updating(
          cur_batch_size, 
          num_features, 
          X_features, 
          pca_features_count_variable, 
          pca_features_mean_variable, 
          pca_features_cov_variable,
          params["eps"]))

      pca_features_eigenvalues_tensor, pca_features_eigenvectors_tensor = tf.linalg.eigh(
        tensor = pca_features_cov_variable) # shape = (seq_len,) & (seq_len, seq_len)

    # Lastly use control dependencies around loss to enforce the mahalanobis variables to be assigned, the control order matters, hence the separate contexts
    with tf.control_dependencies(
      control_inputs = [pca_time_cov_variable, pca_features_cov_variable]):
      with tf.control_dependencies(
        control_inputs = [pca_time_mean_variable, pca_features_mean_variable]):
        with tf.control_dependencies(
          control_inputs = [pca_time_count_variable, pca_features_count_variable]):
          with tf.control_dependencies(
            control_inputs = [tf.assign(ref = pca_time_eigenvalues_variable, value = pca_time_eigenvalues_tensor), 
                              tf.assign(ref = pca_time_eigenvectors_variable, value = pca_time_eigenvectors_tensor),
                              tf.assign(ref = pca_features_eigenvalues_variable, value = pca_features_eigenvalues_tensor), 
                              tf.assign(ref = pca_features_eigenvectors_variable, value = pca_features_eigenvectors_tensor)]):
            loss = tf.reduce_sum(input_tensor = tf.zeros(shape = (), dtype = tf.float64) * dummy_variable)

            train_op = tf.contrib.layers.optimize_loss(
              loss = loss,
              global_step = tf.train.get_global_step(),
              learning_rate = params["learning_rate"],
              optimizer = "SGD")
  else:
    # Time based
    # shape = (cur_batch_size * seq_len, num_features)
    X_time_centered = X_time - pca_time_mean_variable
    # shape = (cur_batch_size * seq_len, params["k_principal_components"])
    X_time_projected = tf.matmul(
      a = X_time_centered, 
      b = pca_time_eigenvectors_variable[:, -params["k_principal_components"]:])
    # shape = (cur_batch_size * seq_len, num_features)
    X_time_reconstructed = tf.matmul(
      a = X_time_projected, 
      b = pca_time_eigenvectors_variable[:, -params["k_principal_components"]:], 
      transpose_b = True)
    # shape = (cur_batch_size * seq_len, num_features)
    X_time_abs_reconstruction_error = tf.abs(
      x = X_time_centered - X_time_reconstructed)

    # Features based
    # shape = (cur_batch_size * num_features, seq_len)
    X_features_centered = X_features - pca_features_mean_variable
    # shape = (cur_batch_size * num_features, params["k_principal_components"])
    X_features_projected = tf.matmul(
      a = X_features_centered, 
      b = pca_features_eigenvectors_variable[:, -params["k_principal_components"]:])
    # shape = (cur_batch_size * num_features, seq_len)
    X_features_reconstructed = tf.matmul(
      a = X_features_projected, 
      b = pca_features_eigenvectors_variable[:, -params["k_principal_components"]:], 
      transpose_b = True)
    # shape = (cur_batch_size * num_features, seq_len)
    X_features_abs_reconstruction_error = tf.abs(
      x = X_features_centered - X_features_reconstructed)

    if mode == tf.estimator.ModeKeys.TRAIN and params["evaluation_mode"] == "calculate_error_distribution_statistics":
      ################################################################################

      with tf.variable_scope(name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
        # Time based ########################################
        singleton_time_condition = tf.equal(
          x = cur_batch_size * params["seq_len"], y = 1) # shape = ()
        
        cov_time_variable, mean_time_variable, count_time_variable = tf.cond(
          pred = singleton_time_condition, 
          true_fn = lambda: singleton_batch_cov_variable_updating(
            params["seq_len"], 
            X_time_abs_reconstruction_error, 
            abs_err_count_time_variable, 
            abs_err_mean_time_variable, 
            abs_err_cov_time_variable,
            params["eps"]), 
          false_fn = lambda: non_singleton_batch_cov_variable_updating(
            cur_batch_size, 
            params["seq_len"], 
            X_time_abs_reconstruction_error, 
            abs_err_count_time_variable, 
            abs_err_mean_time_variable, 
            abs_err_cov_time_variable,
            params["eps"]))

        # Features based ########################################
        singleton_features_condition = tf.equal(
          x = cur_batch_size * num_features, y = 1) # shape = ()
        
        cov_features_variable, mean_features_variable, count_features_variable = tf.cond(
          pred = singleton_features_condition, 
          true_fn = lambda: singleton_batch_cov_variable_updating(
            num_features, 
            X_features_abs_reconstruction_error, 
            abs_err_count_features_variable, 
            abs_err_mean_features_variable, 
            abs_err_cov_features_variable,
            params["eps"]), 
          false_fn = lambda: non_singleton_batch_cov_variable_updating(
            cur_batch_size, 
            num_features, 
            X_features_abs_reconstruction_error, 
            abs_err_count_features_variable, 
            abs_err_mean_features_variable, 
            abs_err_cov_features_variable,
            params["eps"]))

      # Lastly use control dependencies around loss to enforce the mahalanobis variables to be assigned, the control order matters, hence the separate contexts
      with tf.control_dependencies(
        control_inputs = [cov_time_variable, cov_features_variable]):
        with tf.control_dependencies(
          control_inputs = [mean_time_variable, mean_features_variable]):
          with tf.control_dependencies(
            control_inputs = [count_time_variable, count_features_variable]):
            # Time based
            # shape = (num_features, num_features)
            abs_err_inv_cov_time_tensor = \
              tf.matrix_inverse(input = cov_time_variable + \
                tf.eye(num_rows = tf.shape(input = cov_time_variable)[0], 
                     dtype = tf.float64) * params["eps"])
            # Features based
            # shape = (seq_len, seq_len)
            abs_err_inv_cov_features_tensor = \
              tf.matrix_inverse(input = cov_features_variable + \
                tf.eye(num_rows = tf.shape(input = cov_features_variable)[0], 
                     dtype = tf.float64) * params["eps"])
            
            with tf.control_dependencies(
              control_inputs = [tf.assign(ref = abs_err_inv_cov_time_variable, value = abs_err_inv_cov_time_tensor), 
                                tf.assign(ref = abs_err_inv_cov_features_variable, value = abs_err_inv_cov_features_tensor)]):
              loss = tf.reduce_sum(input_tensor = tf.zeros(shape = (), dtype = tf.float64) * dummy_variable)

              train_op = tf.contrib.layers.optimize_loss(
                loss = loss,
                global_step = tf.train.get_global_step(),
                learning_rate = params["learning_rate"],
                optimizer = "SGD")
    elif mode == tf.estimator.ModeKeys.EVAL and params["evaluation_mode"] != "tune_anomaly_thresholds":
      # Reconstruction loss on evaluation set
      loss = tf.losses.mean_squared_error(labels = X_time_centered, predictions = X_time_abs_reconstruction_error)

      if params["evaluation_mode"] == "reconstruction":
        # Reconstruction eval metrics
        eval_metric_ops = {
          "rmse": tf.metrics.root_mean_squared_error(labels = X_time_centered, predictions = X_time_abs_reconstruction_error),
          "mae": tf.metrics.mean_absolute_error(labels = X_time_centered, predictions = X_time_abs_reconstruction_error)
        }
    elif mode == tf.estimator.ModeKeys.PREDICT or ((mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL) and params["evaluation_mode"] == "tune_anomaly_thresholds"):
      with tf.variable_scope(name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
        # Time based
        mahalanobis_distance_time = mahalanobis_distance(
          error_vectors_reshaped = X_time_abs_reconstruction_error,
          mean_vector = abs_err_mean_time_variable, 
          inv_covariance = abs_err_inv_cov_time_variable, 
          final_shape = params["seq_len"]) # shape = (cur_batch_size, seq_len)
        
        # Features based
        mahalanobis_distance_features = mahalanobis_distance(
          error_vectors_reshaped = X_features_abs_reconstruction_error,
          mean_vector = abs_err_mean_features_variable, 
          inv_covariance = abs_err_inv_cov_features_variable,
          final_shape = num_features) # shape = (cur_batch_size, num_features)

      if mode != tf.estimator.ModeKeys.PREDICT:
        labels_normal_mask = tf.equal(x = labels, y = 0)
        labels_anomalous_mask = tf.equal(x = labels, y = 1)

        if mode == tf.estimator.ModeKeys.TRAIN:
          with tf.variable_scope(
            name_or_scope = "mahalanobis_distance_variables", reuse = tf.AUTO_REUSE):
            # Time based
            # shape = (num_time_anomaly_thresholds,)
            time_anomaly_thresholds = tf.linspace(
              start = tf.constant(value = params["min_time_anomaly_threshold"], dtype = tf.float64),
              stop = tf.constant(value = params["max_time_anomaly_threshold"], dtype = tf.float64), 
              num = params["num_time_anomaly_thresholds"])

            tp_time_update_op, fn_time_update_op, fp_time_update_op, tn_time_update_op = \
              update_anomaly_threshold_variables(
                labels_normal_mask, 
                labels_anomalous_mask, 
                params["num_time_anomaly_thresholds"], 
                time_anomaly_thresholds, 
                mahalanobis_distance_time, 
                tp_at_thresholds_time_variable, 
                fn_at_thresholds_time_variable, 
                fp_at_thresholds_time_variable, 
                tn_at_thresholds_time_variable,
                mode)

            # Features based
            # shape = (num_features_anomaly_thresholds,)
            features_anomaly_thresholds = tf.linspace(
              start = tf.constant(value = params["min_features_anomaly_threshold"], dtype = tf.float64),
              stop = tf.constant(value = params["max_features_anomaly_threshold"], dtype = tf.float64), 
              num = params["num_features_anomaly_thresholds"])

            tp_features_update_op, fn_features_update_op, fp_features_update_op, tn_features_update_op = \
              update_anomaly_threshold_variables(
                labels_normal_mask, 
                labels_anomalous_mask, 
                params["num_features_anomaly_thresholds"], 
                features_anomaly_thresholds, 
                mahalanobis_distance_features, 
                tp_at_thresholds_features_variable, 
                fn_at_thresholds_features_variable, 
                fp_at_thresholds_features_variable, 
                tn_at_thresholds_features_variable, 
                mode)

          # Reconstruction loss on evaluation set
          with tf.control_dependencies(
            control_inputs = [
              tp_time_update_op, 
              fn_time_update_op, 
              fp_time_update_op, 
              tn_time_update_op, 
              tp_features_update_op, 
              fn_features_update_op, 
              fp_features_update_op, 
              tn_features_update_op]):
            # Time based
            acc_time, pre_time, rec_time, f_beta_score_time = \
              calculate_composite_classification_metrics(
                time_anomaly_thresholds, 
                tp_at_thresholds_time_variable, 
                fn_at_thresholds_time_variable, 
                fp_at_thresholds_time_variable, 
                tn_at_thresholds_time_variable,
                params["f_score_beta"])

            # Features based
            acc_features, pre_features, rec_features, f_beta_score_features = \
              calculate_composite_classification_metrics(
                features_anomaly_thresholds, 
                tp_at_thresholds_features_variable, 
                fn_at_thresholds_features_variable, 
                fp_at_thresholds_features_variable, 
                tn_at_thresholds_features_variable,
                params["f_score_beta"])

            with tf.control_dependencies(
              control_inputs = [pre_time, pre_features]):
              with tf.control_dependencies(
                control_inputs = [rec_time, rec_features]):
                with tf.control_dependencies(
                  control_inputs = [f_beta_score_time, f_beta_score_features]):
                  # Time based
                  best_anomaly_threshold_time = find_best_anomaly_threshold(
                    time_anomaly_thresholds, 
                    f_beta_score_time, 
                    params["time_anomaly_threshold"], 
                    time_anomaly_threshold_variable)

                  # Features based
                  best_anomaly_threshold_features = find_best_anomaly_threshold(
                    features_anomaly_thresholds, 
                    f_beta_score_features, 
                    params["features_anomaly_threshold"], 
                    features_anomaly_threshold_variable)

                  with tf.control_dependencies(
                    control_inputs = [
                      tf.assign(
                        ref = time_anomaly_threshold_variable, 
                        value = best_anomaly_threshold_time), 
                      tf.assign(ref = 
                                features_anomaly_threshold_variable, 
                                value = best_anomaly_threshold_features)]):

                    loss = tf.reduce_sum(
                      input_tensor = tf.zeros(shape = (), dtype = tf.float64) * dummy_variable)

                    train_op = tf.contrib.layers.optimize_loss(
                      loss = loss,
                      global_step = tf.train.get_global_step(),
                      learning_rate = params["learning_rate"],
                      optimizer = "SGD")
        elif mode == tf.estimator.ModeKeys.EVAL:
          with tf.variable_scope(
            name_or_scope = "anomaly_threshold_eval_variables", reuse = tf.AUTO_REUSE):
            # Time based
            tp_time_update_op, fn_time_update_op, fp_time_update_op, tn_time_update_op = \
              update_anomaly_threshold_variables(
                labels_normal_mask, 
                labels_anomalous_mask, 
                1,
                time_anomaly_threshold_variable, 
                mahalanobis_distance_time, 
                tp_at_threshold_eval_time_variable, 
                fn_at_threshold_eval_time_variable, 
                fp_at_threshold_eval_time_variable, 
                tn_at_threshold_eval_time_variable,
                mode)

            # Features based
            tp_features_update_op, fn_features_update_op, fp_features_update_op, tn_features_update_op = \
              update_anomaly_threshold_variables(
                labels_normal_mask, 
                labels_anomalous_mask, 
                1,
                features_anomaly_threshold_variable, 
                mahalanobis_distance_features, 
                tp_at_threshold_eval_features_variable, 
                fn_at_threshold_eval_features_variable, 
                fp_at_threshold_eval_features_variable, 
                tn_at_threshold_eval_features_variable,
                mode)

          with tf.variable_scope(
            name_or_scope = "anomaly_threshold_eval_variables", reuse = tf.AUTO_REUSE):
            # Time based
            acc_time_update_op, pre_time_update_op, rec_time_update_op, f_beta_score_time_update_op = \
              calculate_composite_classification_metrics(
                time_anomaly_threshold_variable, 
                tp_at_threshold_eval_time_variable, 
                fn_at_threshold_eval_time_variable, 
                fp_at_threshold_eval_time_variable, 
                tn_at_threshold_eval_time_variable,
                params["f_score_beta"]) 

            # Features based
            acc_features_update_op, pre_features_update_op, rec_features_update_op, f_beta_score_features_update_op = \
              calculate_composite_classification_metrics(
                features_anomaly_threshold_variable, 
                tp_at_threshold_eval_features_variable, 
                fn_at_threshold_eval_features_variable, 
                fp_at_threshold_eval_features_variable, 
                tn_at_threshold_eval_features_variable,
                params["f_score_beta"]) 

          loss = tf.losses.mean_squared_error(labels = X_time_centered, predictions = X_time_reconstructed)

          acc_at_threshold_eval_time_variable = tf.cast(x = tp_at_threshold_eval_time_variable + tn_at_threshold_eval_time_variable, dtype = tf.float64) \
            / tf.cast(x = tp_at_threshold_eval_time_variable + fn_at_threshold_eval_time_variable + fp_at_threshold_eval_time_variable + tn_at_threshold_eval_time_variable, dtype = tf.float64)
          pre_at_threshold_eval_time_variable = tf.cast(x = tp_at_threshold_eval_time_variable, dtype = tf.float64) \
            / tf.cast(x = tp_at_threshold_eval_time_variable + fp_at_threshold_eval_time_variable, dtype = tf.float64)
          rec_at_threshold_eval_time_variable = tf.cast(x = tp_at_threshold_eval_time_variable, dtype = tf.float64) \
            / tf.cast(x = tp_at_threshold_eval_time_variable + fn_at_threshold_eval_time_variable, dtype = tf.float64)
          f_beta_score_at_threshold_eval_time_variable = (1.0 + params["f_score_beta"] ** 2) * pre_at_threshold_eval_time_variable * rec_at_threshold_eval_time_variable \
            / (params["f_score_beta"] ** 2 * pre_at_threshold_eval_time_variable + rec_at_threshold_eval_time_variable)

          acc_at_threshold_eval_features_variable = tf.cast(x = tp_at_threshold_eval_features_variable + tn_at_threshold_eval_features_variable, dtype = tf.float64) \
            / tf.cast(x = tp_at_threshold_eval_features_variable + fn_at_threshold_eval_features_variable + fp_at_threshold_eval_features_variable + tn_at_threshold_eval_features_variable, dtype = tf.float64)
          pre_at_threshold_eval_features_variable = tf.cast(x = tp_at_threshold_eval_features_variable, dtype = tf.float64) \
            / tf.cast(x = tp_at_threshold_eval_features_variable + fp_at_threshold_eval_features_variable, dtype = tf.float64)
          rec_at_threshold_eval_features_variable = tf.cast(x = tp_at_threshold_eval_features_variable, dtype = tf.float64) \
            / tf.cast(x = tp_at_threshold_eval_features_variable + fn_at_threshold_eval_features_variable, dtype = tf.float64)
          f_beta_score_at_threshold_eval_features_variable = (1.0 + params["f_score_beta"] ** 2) * pre_at_threshold_eval_features_variable * rec_at_threshold_eval_features_variable \
            / (params["f_score_beta"] ** 2 * pre_at_threshold_eval_features_variable + rec_at_threshold_eval_features_variable)

          # Anomaly detection eval metrics
          eval_metric_ops = {
            # Time based
            "time_anomaly_tp": (tp_at_threshold_eval_time_variable, tp_time_update_op),
            "time_anomaly_fn": (fn_at_threshold_eval_time_variable, fn_time_update_op),
            "time_anomaly_fp": (fp_at_threshold_eval_time_variable, fp_time_update_op),
            "time_anomaly_tn": (tn_at_threshold_eval_time_variable, tn_time_update_op),

            "time_anomaly_acc": (acc_at_threshold_eval_time_variable, acc_time_update_op),
            "time_anomaly_pre": (pre_at_threshold_eval_time_variable, pre_time_update_op),
            "time_anomaly_rec": (rec_at_threshold_eval_time_variable, rec_time_update_op),
            "time_anomaly_f_beta_score": (f_beta_score_at_threshold_eval_time_variable, f_beta_score_time_update_op),

             # Features based
            "features_anomaly_tp": (tp_at_threshold_eval_features_variable, tp_features_update_op),
            "features_anomaly_fn": (fn_at_threshold_eval_features_variable, fn_features_update_op),
            "features_anomaly_fp": (fp_at_threshold_eval_features_variable, fp_features_update_op),
            "features_anomaly_tn": (tn_at_threshold_eval_features_variable, tn_features_update_op),

            "features_anomaly_acc": (acc_at_threshold_eval_features_variable, acc_features_update_op),
            "features_anomaly_pre": (pre_at_threshold_eval_features_variable, pre_features_update_op),
            "features_anomaly_rec": (rec_at_threshold_eval_features_variable, rec_features_update_op),
            "features_anomaly_f_beta_score": (f_beta_score_at_threshold_eval_features_variable, f_beta_score_features_update_op)
          }
      else: # mode == tf.estimator.ModeKeys.PREDICT
        # Flag predictions as either normal or anomalous
        time_anomaly_flags = tf.where(
          condition = tf.reduce_any(
            input_tensor = tf.greater(
              x = tf.abs(x = mahalanobis_distance_time),
              y = time_anomaly_threshold_variable), 
            axis = 1), 
          x = tf.ones(shape = [cur_batch_size], dtype = tf.int64), 
          y = tf.zeros(shape = [cur_batch_size], dtype = tf.int64)) # shape = (cur_batch_size,)

        features_anomaly_flags = tf.where(
          condition = tf.reduce_any(
            input_tensor = tf.greater(
              x = tf.abs(x = mahalanobis_distance_features),
              y = features_anomaly_threshold_variable), 
            axis = 1), 
          x = tf.ones(shape = [cur_batch_size], dtype = tf.int64), 
          y = tf.zeros(shape = [cur_batch_size], dtype = tf.int64)) # shape = (cur_batch_size,)

        # Create predictions dictionary
        predictions_dict = {
          "X_time_abs_reconstruction_error": tf.reshape(
            tensor = X_time_abs_reconstruction_error, 
            shape = [cur_batch_size, params["seq_len"], num_features]), 
          "X_features_abs_reconstruction_error": tf.transpose(
            a = tf.reshape(
              tensor = X_features_abs_reconstruction_error, 
              shape = [cur_batch_size, num_features, params["seq_len"]]), 
            perm = [0, 2, 1]),
          "mahalanobis_distance_time": mahalanobis_distance_time, 
          "mahalanobis_distance_features": mahalanobis_distance_features, 
          "time_anomaly_flags": time_anomaly_flags, 
          "features_anomaly_flags": features_anomaly_flags}

        # Create export outputs
        export_outputs = {
          "predict_export_outputs": tf.estimator.export.PredictOutput(
            outputs = predictions_dict)}

  # Return EstimatorSpec
  return tf.estimator.EstimatorSpec(
    mode = mode,
    predictions = predictions_dict,
    loss = loss,
    train_op = train_op,
    eval_metric_ops = eval_metric_ops,
    export_outputs = export_outputs)

# Create our serving input function to accept the data at serving and send it in the 
# right format to our custom estimator
def serving_input_fn(seq_len):
    # This function fixes the shape and type of our input strings
    def fix_shape_and_type_for_serving(placeholder):
        current_batch_size = tf.shape(input = placeholder, out_type = tf.int64)[0]
        
        # String split each string in batch and output values from the resulting SparseTensors
        split_string = tf.stack(values = tf.map_fn( # shape = (batch_size, seq_len)
            fn = lambda x: tf.string_split(source = [placeholder[x]], delimiter = ',').values, 
            elems = tf.range(start = 0, limit = current_batch_size, dtype = tf.int64), 
            dtype = tf.string), axis = 0)
        
        # Convert each string in the split tensor to float
        # shape = (batch_size, seq_len)
        feature_tensor = tf.string_to_number(string_tensor = split_string, out_type = tf.float64)
        
        return feature_tensor
    
    # This function fixes dynamic shape ambiguity of last dimension so that we will be able to 
    # use it in our DNN (since tf.layers.dense require the last dimension to be known)
    def get_shape_and_set_modified_shape_2D(tensor, additional_dimension_sizes):
        # Get static shape for tensor and convert it to list
        shape = tensor.get_shape().as_list()
        # Set outer shape to additional_dimension_sizes[0] since know this is the correct size
        shape[1] = additional_dimension_sizes[0]
        # Set the shape of tensor to our modified shape
        tensor.set_shape(shape = shape) # shape = (batch_size, additional_dimension_sizes[0])

        return tensor
            
    # Create placeholders to accept the data sent to the model at serving time
    # All features come in as a batch of strings, shape = (batch_size,), 
    # this was so because of passing the arrays to online ml-engine prediction
    feature_placeholders = {
        feature: tf.placeholder(
          dtype = tf.string, shape = [None]) for feature in UNLABELED_CSV_COLUMNS
    }
    
    # Create feature tensors
    features = {key: fix_shape_and_type_for_serving(placeholder = tensor) 
      for key, tensor in feature_placeholders.items()}
    
    # Fix dynamic shape ambiguity of feature tensors for our DNN
    features = {key: get_shape_and_set_modified_shape_2D(
      tensor = tensor, additional_dimension_sizes = [seq_len]) for key, tensor in features.items()}

    return tf.estimator.export.ServingInputReceiver(
      features = features, receiver_tensors = feature_placeholders)

# Create estimator to train and evaluate
def train_and_evaluate(args):
  # Create our custom estimator using our model function
  estimator = tf.estimator.Estimator(
    model_fn = pca_anomaly_detection,
    model_dir = args["output_dir"],
    params = {
      "seq_len": args["seq_len"],
      "learning_rate": args["learning_rate"],
      "evaluation_mode": args["evaluation_mode"],
      "k_principal_components": args["k_principal_components"],
      "num_time_anomaly_thresholds": args["num_time_anomaly_thresholds"],
      "num_features_anomaly_thresholds": args["num_features_anomaly_thresholds"],
      "min_time_anomaly_threshold": args["min_time_anomaly_threshold"],
      "max_time_anomaly_threshold": args["max_time_anomaly_threshold"],
      "min_features_anomaly_threshold": args["min_features_anomaly_threshold"],
      "max_features_anomaly_threshold": args["max_features_anomaly_threshold"],
      "time_anomaly_threshold": args["time_anomaly_threshold"], 
      "features_anomaly_threshold": args["features_anomaly_threshold"],
      "eps": args["eps"],
      "f_score_beta": args["f_score_beta"]})
  
  if args["evaluation_mode"] == "reconstruction":
    # Create train spec to read in our training data
    train_spec = tf.estimator.TrainSpec(
      input_fn = read_dataset(
        filename = args["train_file_pattern"],
        mode = tf.estimator.ModeKeys.TRAIN, 
        batch_size = args["train_batch_size"],
        params = args),
      max_steps = args["train_steps"]) 

    # Create eval spec to read in our validation data and export our model
    eval_spec = tf.estimator.EvalSpec(
      input_fn = read_dataset(
        filename = args["eval_file_pattern"], 
        mode = tf.estimator.ModeKeys.EVAL, 
        batch_size = args["eval_batch_size"],
        params = args),
      steps = None,
      start_delay_secs = args["start_delay_secs"], # start evaluating after N seconds
      throttle_secs = args["throttle_secs"])  # evaluate every N seconds

    # Create train and evaluate loop to train and evaluate our estimator
    tf.estimator.train_and_evaluate(
      estimator = estimator, train_spec = train_spec, eval_spec = eval_spec)
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
      exporter = tf.estimator.LatestExporter(
        name = "exporter", serving_input_receiver_fn = lambda: serving_input_fn(args["seq_len"]))

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
      throttle_secs = args["throttle_secs"])  # evaluate every N seconds
    
    # Create train and evaluate loop to train and evaluate our estimator
    tf.estimator.train_and_evaluate(
      estimator = estimator, train_spec = train_spec, eval_spec = eval_spec)
