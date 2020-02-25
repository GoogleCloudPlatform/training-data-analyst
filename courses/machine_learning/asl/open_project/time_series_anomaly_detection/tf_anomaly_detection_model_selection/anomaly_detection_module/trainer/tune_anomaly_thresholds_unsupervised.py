import tensorflow as tf

from .calculate_error_distribution_statistics import non_singleton_batch_var_variable_updating
from .calculate_error_distribution_statistics import singleton_batch_var_variable_updating
from .predict import flag_anomalies_by_thresholding


def tune_anomaly_thresholds_unsupervised_training(
    cur_batch_size,
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
  """Tunes anomaly thresholds during unsupervised training mode.

  Given dimensions of inputs, mahalanobis distances, and variables tracking
  counts, means, and variances of mahalanobis distance, returns loss and
  train_op.

  Args:
    cur_batch_size: Current batch size, could be partially filled.
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
        shape=[cur_batch_size * params["num_feat"]])

    singleton_feat_condition = tf.equal(
        x=cur_batch_size * params["num_feat"], y=1)

    var_feat_var, mean_feat_var, count_feat_var = tf.cond(
        pred=singleton_feat_condition,
        true_fn=lambda: singleton_batch_var_variable_updating(
            params["num_feat"],
            mahalanobis_dist_feat_flat,
            count_thresh_feat_var,
            mean_thresh_feat_var,
            var_thresh_feat_var),
        false_fn=lambda: non_singleton_batch_var_variable_updating(
            cur_batch_size,
            params["num_feat"],
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


def tune_anomaly_thresholds_unsupervised_eval(
    cur_batch_size,
    time_anom_thresh_var,
    mahalanobis_dist_time,
    feat_anom_thresh_var,
    mahalanobis_dist_feat):
  """Checks tuned anomaly thresholds during supervised evaluation mode.

  Given dimensions of inputs, mahalanobis distances, and variables tracking
  counts, means, and variances of mahalanobis distance, returns loss and
  train_op.

  Args:
    cur_batch_size: Current batch size, could be partially filled.
    time_anom_thresh_var: Time anomaly threshold variable.
    mahalanobis_dist_time: Time major mahalanobis distance.
    feat_anom_thresh_var: Feature anomaly threshold variable.
    mahalanobis_dist_feat: Feature major mahalanobis distance.

  Returns:
    loss: The scalar loss to tie our updates back to Estimator graph.
    eval_metric_ops: Evaluation metrics of threshold tuning.
  """
  loss = tf.zeros(shape=[], dtype=tf.float64)

  # Flag predictions as either normal or anomalous
  # shape = (cur_batch_size,)
  time_anom_flags = flag_anomalies_by_thresholding(
      cur_batch_size, mahalanobis_dist_time, time_anom_thresh_var)

  # shape = (cur_batch_size,)
  feat_anom_flags = flag_anomalies_by_thresholding(
      cur_batch_size, mahalanobis_dist_feat, feat_anom_thresh_var)

  # Anomaly detection eval metrics
  eval_metric_ops = {
      # Time based
      "time_anom_tp": tf.metrics.mean(values=time_anom_flags),

      # Features based
      "feat_anom_tp": tf.metrics.mean(values=feat_anom_flags)
  }

  return loss, eval_metric_ops
