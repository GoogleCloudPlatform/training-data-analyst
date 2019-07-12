import tensorflow as tf

from .autoencoder_dense import dense_autoencoder_model
from .autoencoder_lstm import lstm_enc_dec_autoencoder_model
from .autoencoder_pca import pca_model
from .calculate_error_distribution_statistics import calculate_error_distribution_statistics_training
from .calculate_error_distribution_statistics import mahalanobis_dist
from .error_distribution_vars import create_both_mahalanobis_dist_vars
from .predict import anomaly_detection_predictions
from .reconstruction import reconstruction_evaluation
from .tune_anomaly_threshold_vars import create_both_confusion_matrix_thresh_vars
from .tune_anomaly_threshold_vars import create_both_mahalanobis_unsupervised_thresh_vars
from .tune_anomaly_thresholds_supervised import tune_anomaly_thresholds_supervised_training
from .tune_anomaly_thresholds_supervised import tune_anomaly_thresholds_supervised_eval
from .tune_anomaly_thresholds_unsupervised import tune_anomaly_thresholds_unsupervised_training
from .tune_anomaly_thresholds_unsupervised import tune_anomaly_thresholds_unsupervised_eval


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
      input=features[params["feat_names"][0]], out_type=tf.int64)[0]

  # Stack all of the features into a 3-D tensor
  # shape = (cur_batch_size, seq_len, num_feat)
  X = tf.stack(
      values=[features[key] for key in params["feat_names"]], axis=2)

  ##############################################################################
  
  # Important to note that flags determining which variables should be created 
  # need to remain the same through all stages or else they won't be in the
  # checkpoint.

  # Variables for calculating error distribution statistics
  (abs_err_count_time_var,
   abs_err_mean_time_var,
   abs_err_cov_time_var,
   abs_err_inv_cov_time_var,
   abs_err_count_feat_var,
   abs_err_mean_feat_var,
   abs_err_cov_feat_var,
   abs_err_inv_cov_feat_var) = create_both_mahalanobis_dist_vars(
       seq_len=params["seq_len"], num_feat=params["num_feat"])

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
         scope="anom_thresh_eval_vars",
         time_thresh_size=[],
         feat_thresh_size=[])

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
    model_function(X, mode, params, cur_batch_size, dummy_var)

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
            final_shape=params["num_feat"])

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
            loss, eval_metric_ops = tune_anomaly_thresholds_supervised_eval(
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
          elif mode == tf.estimator.ModeKeys.EVAL:
            loss, eval_metric_ops = tune_anomaly_thresholds_unsupervised_eval(
                cur_batch_size,
                time_anom_thresh_var,
                mahalanobis_dist_time,
                feat_anom_thresh_var,
                mahalanobis_dist_feat)
      else:  # mode == tf.estimator.ModeKeys.PREDICT
        predictions_dict, export_outputs = anomaly_detection_predictions(
            cur_batch_size,
            params["seq_len"],
            params["num_feat"],
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
