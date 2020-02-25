import tensorflow as tf


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
