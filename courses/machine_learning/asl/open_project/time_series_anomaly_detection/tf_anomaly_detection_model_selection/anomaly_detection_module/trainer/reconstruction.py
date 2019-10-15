import tensorflow as tf


def reconstruction_evaluation(X_time_orig, X_time_recon, training_mode):
  """Reconstruction loss on evaluation set.

  Given time major original and reconstructed features data and the training
  mode, return loss and eval_metrics_ops.

  Args:
    X_time_orig: Time major original features data.
    X_time_recon: Time major reconstructed features data.
    training_mode: Current training mode.

  Returns:
    loss: Scalar reconstruction loss.
    eval_metric_ops: Evaluation metrics of reconstruction.
  """
  loss = tf.losses.mean_squared_error(
      labels=X_time_orig, predictions=X_time_recon)

  eval_metric_ops = None

  if training_mode == "reconstruction":
    # Reconstruction eval metrics
    eval_metric_ops = {
        "rmse": tf.metrics.root_mean_squared_error(
            labels=X_time_orig, predictions=X_time_recon),
        "mae": tf.metrics.mean_absolute_error(
            labels=X_time_orig, predictions=X_time_recon)
    }

  return loss, eval_metric_ops
