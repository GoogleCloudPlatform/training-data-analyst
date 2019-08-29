import tensorflow as tf


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
