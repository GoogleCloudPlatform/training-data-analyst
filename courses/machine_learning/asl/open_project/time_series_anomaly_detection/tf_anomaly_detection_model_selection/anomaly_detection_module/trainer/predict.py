import tensorflow as tf


def flag_anomalies_by_thresholding(
    cur_batch_size, mahalanobis_dist, anom_thresh_var):
  """Flags anomalies by thresholding.

  Given current batch size, mahalanobis distance, and anomaly threshold
  variable, return predicted anomaly flags.

  Args:
    cur_batch_size: Current batch size, could be partially filled.
    mahalanobis_dist: Mahalanobis distance.
    anom_thresh_var: Anomaly threshold variable.

  Returns:
    anomaly_flags: tf.int64 vector of current batch size elements of
    0's and 1's indicating if each sequence is anomalous or not.
  """
  anom_flags = tf.where(
      condition=tf.reduce_any(
          input_tensor=tf.greater(
              x=tf.abs(x=mahalanobis_dist),
              y=anom_thresh_var),
          axis=1),
      x=tf.ones(shape=[cur_batch_size], dtype=tf.int64),
      y=tf.zeros(shape=[cur_batch_size], dtype=tf.int64))

  return anom_flags


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
  time_anom_flags = flag_anomalies_by_thresholding(
      cur_batch_size, mahalanobis_dist_time, time_anom_thresh_var)

  # shape = (cur_batch_size,)
  feat_anom_flags = flag_anomalies_by_thresholding(
      cur_batch_size, mahalanobis_dist_feat, feat_anom_thresh_var)

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
      "time_anom_thresh_var": tf.fill(
          dims=[cur_batch_size], value=time_anom_thresh_var),
      "feat_anom_thresh_var": tf.fill(
          dims=[cur_batch_size], value=feat_anom_thresh_var),
      "time_anom_flags": time_anom_flags,
      "feat_anom_flags": feat_anom_flags}

  # Create export outputs
  export_outputs = {
      "predict_export_outputs": tf.estimator.export.PredictOutput(
          outputs=predictions_dict)
  }

  return predictions_dict, export_outputs
