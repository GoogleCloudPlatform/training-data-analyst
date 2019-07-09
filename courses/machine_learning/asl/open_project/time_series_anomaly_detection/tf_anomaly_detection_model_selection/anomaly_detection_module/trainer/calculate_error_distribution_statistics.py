import tensorflow as tf


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
        value_b=tf.reshape(tensor=x, shape=[1, 1]),
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
        x=cur_batch_size * params["num_feat"], y=1)

    cov_feat_var, mean_feat_var, count_feat_var = tf.cond(
        pred=singleton_feat_condition,
        true_fn=lambda: singleton_batch_cov_variable_updating(
            params["num_feat"],
            X_feat_abs_recon_err,
            abs_err_count_feat_var,
            abs_err_mean_feat_var,
            abs_err_cov_feat_var),
        false_fn=lambda: non_singleton_batch_cov_variable_updating(
            cur_batch_size,
            params["num_feat"],
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
