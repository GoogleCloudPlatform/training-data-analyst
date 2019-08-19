import tensorflow as tf


def calculate_threshold_confusion_matrix(labels_mask, preds, num_thresh):
  """Calculates confusion matrix based on thresholds.

  Given labels mask, predictions, and number of thresholds, returns count
  for cell in confusion matrix.

  Args:
    labels_mask: tf.bool vector tensor when label was normal or
      anomalous.
    preds: Predicted anomaly labels.
    num_thresh: Number of anomaly thresholds to try in parallel grid search.

  Returns:
    Count for cell in confusion matrix.
  """
  count = tf.reduce_sum(
      input_tensor=tf.cast(
          x=tf.map_fn(
              fn=lambda threshold: tf.logical_and(
                  x=labels_mask,
                  y=preds[threshold, :]),
              elems=tf.range(start=0, limit=num_thresh, dtype=tf.int64),
              dtype=tf.bool),
          dtype=tf.int64),
      axis=1)

  return count


def update_anom_thresh_vars(
    labels_norm_mask,
    labels_anom_mask,
    num_thresh,
    anom_thresh,
    mahalanobis_dist,
    tp_at_thresh_var,
    fn_at_thresh_var,
    fp_at_thresh_var,
    tn_at_thresh_var,
    mode):
  """Updates anomaly threshold variables.

  Given masks for when labels are normal and anomalous, the number of anomaly
  thresholds and the thresholds themselves, the mahalanobis distance, variables
  for the confusion matrix, and the current Estimator mode, returns the updated
  variables for the confusion matrix.

  Args:
    labels_norm_mask: tf.bool vector tensor that is true when label was normal.
    labels_anom_mask: tf.bool vector tensor that is true when label was
      anomalous.
    num_thresh: Number of anomaly thresholds to try in parallel grid search.
    anom_thresh: tf.float64 vector tensor of grid of anomaly thresholds to try.
    mahalanobis_dist: tf.float64 matrix tensor of mahalanobis distances across
      batch.
    tp_at_thresh_var: tf.int64 variable tracking number of true positives at
      each possible anomaly threshold.
    fn_at_thresh_var: tf.int64 variable tracking number of false negatives at
      each possible anomaly threshold.
    fp_at_thresh_var: tf.int64 variable tracking number of false positives at
      each possible anomaly threshold.
    tn_at_thresh_var: tf.int64 variable tracking number of true negatives at
      each possible anomaly threshold.
    mode: Estimator ModeKeys, can take values of TRAIN and EVAL.

  Returns:
    Updated confusion matrix variables.
  """
  if mode == tf.estimator.ModeKeys.TRAIN:
    # time_shape = (num_time_anom_thresh, cur_batch_size, seq_len)
    # feat_shape = (num_feat_anom_thresh, cur_batch_size, num_feat)
    mahalanobis_dist_over_thresh = tf.map_fn(
        fn=lambda anom_threshold: mahalanobis_dist > anom_threshold,
        elems=anom_thresh,
        dtype=tf.bool)
  else:
    # time_shape = (cur_batch_size, seq_len)
    # feat_shape = (cur_batch_size, num_feat)
    mahalanobis_dist_over_thresh = mahalanobis_dist > anom_thresh

  # time_shape = (num_time_anom_thresh, cur_batch_size)
  # feat_shape = (num_feat_anom_thresh, cur_batch_size)
  mahalanobis_dist_any_over_thresh = tf.reduce_any(
      input_tensor=mahalanobis_dist_over_thresh, axis=-1)

  if mode == tf.estimator.ModeKeys.EVAL:
    # time_shape = (1, cur_batch_size)
    # feat_shape = (1, cur_batch_size)
    mahalanobis_dist_any_over_thresh = tf.expand_dims(
        input=mahalanobis_dist_any_over_thresh, axis=0)

  # time_shape = (num_time_anom_thresh, cur_batch_size)
  # feat_shape = (num_feat_anom_thresh, cur_batch_size)
  predicted_normals = tf.equal(
      x=mahalanobis_dist_any_over_thresh, y=False)

  # time_shape = (num_time_anom_thresh, cur_batch_size)
  # feat_shape = (num_feat_anom_thresh, cur_batch_size)
  predicted_anomalies = tf.equal(
      x=mahalanobis_dist_any_over_thresh, y=True)

  # Calculate confusion matrix of current batch
  # time_shape = (num_time_anom_thresh,)
  # feat_shape = (num_feat_anom_thresh,)
  tp = calculate_threshold_confusion_matrix(
      labels_anom_mask, predicted_anomalies, num_thresh)

  fn = calculate_threshold_confusion_matrix(
      labels_anom_mask, predicted_normals, num_thresh)

  fp = calculate_threshold_confusion_matrix(
      labels_norm_mask, predicted_anomalies, num_thresh)

  tn = calculate_threshold_confusion_matrix(
      labels_norm_mask, predicted_normals, num_thresh)

  if mode == tf.estimator.ModeKeys.EVAL:
    # shape = ()
    tp = tf.squeeze(input=tp)
    fn = tf.squeeze(input=fn)
    fp = tf.squeeze(input=fp)
    tn = tf.squeeze(input=tn)

  with tf.control_dependencies(
      control_inputs=[tf.assign_add(ref=tp_at_thresh_var, value=tp),
                      tf.assign_add(ref=fn_at_thresh_var, value=fn),
                      tf.assign_add(ref=fp_at_thresh_var, value=fp),
                      tf.assign_add(ref=tn_at_thresh_var, value=tn)]):

    return (tf.identity(input=tp_at_thresh_var),
            tf.identity(input=fn_at_thresh_var),
            tf.identity(input=fp_at_thresh_var),
            tf.identity(input=tn_at_thresh_var))


def calculate_composite_classification_metrics(tp, fn, fp, tn, f_score_beta):
  """Calculates compositive classification metrics from the confusion matrix.

  Given variables for the confusion matrix and the value of beta for f-beta
  score, returns accuracy, precision, recall, and f-beta score composite
  metrics.

  Args:
    tp: tf.int64 variable tracking number of true positives at
      each possible anomaly threshold.
    fn: tf.int64 variable tracking number of false negatives at
      each possible anomaly threshold.
    fp: tf.int64 variable tracking number of false positives at
      each possible anomaly threshold.
    tn: tf.int64 variable tracking number of true negatives at
      each possible anomaly threshold.
    f_score_beta: Value of beta for f-beta score.

  Returns:
    Accuracy, precision, recall, and f-beta score composite metric tensors.
  """
  # time_shape = (num_time_anom_thresh,)
  # feat_shape = (num_feat_anom_thresh,)
  acc = tf.cast(x=tp + tn, dtype=tf.float64) \
    / tf.cast(x=tp + fn + fp + tn, dtype=tf.float64)
  tp_float64 = tf.cast(x=tp, dtype=tf.float64)
  pre = tp_float64 / tf.cast(x=tp + fp, dtype=tf.float64)
  rec = tp_float64 / tf.cast(x=tp + fn, dtype=tf.float64)
  f_beta_numerator = (1.0 + f_score_beta ** 2) * (pre * rec)
  f_beta_score = f_beta_numerator / (f_score_beta ** 2 * pre + rec)

  return acc, pre, rec, f_beta_score


def find_best_anom_thresh(
    anom_threshs, f_beta_score, anom_thresh_var):
  """Find best anomaly threshold to use for anomaly classification.

  Given vector of anomaly thresholds and the value of beta for f-beta score,
  returns updated variable that stores the best anomaly threshold value.

  Args:
    anom_threshs: tf.float64 vector tensor of grid of anomaly thresholds to try.
    f_beta_score: tf.float64 vector tensor of f-beta scores for each anomaly
      threshold.
    anom_thresh_var: tf.float64 variable that stores anomaly threshold value.

  Returns:
    Updated variable that stores the anomaly threshold value.
  """
  # shape = ()
  best_anom_thresh = tf.gather(
      params=anom_threshs, indices=tf.argmax(input=f_beta_score, axis=0))

  with tf.control_dependencies(
      control_inputs=[tf.assign(
          ref=anom_thresh_var, value=best_anom_thresh)]):

    return tf.identity(input=anom_thresh_var)


def optimize_anomaly_theshold(
    var_name,
    labels_norm_mask,
    labels_anom_mask,
    mahalanobis_dist,
    tp_thresh_var,
    fn_thresh_var,
    fp_thresh_var,
    tn_thresh_var,
    params,
    mode,
    anom_thresh_var):
  """Optimizes anomaly threshold for anomaly classification.

  Given variable name, label masks, mahalanobis distance, variables for
  confusion matrix, and dictionary of parameters, returns accuracy, precision,
  recall, and f-beta score composite metrics.

  Args:
    var_name: String denoting which set of variables to use. Values are
      "time" and "feat".
    labels_norm_mask: tf.bool vector mask of labels for normals.
    labels_anom_mask: tf.bool vector mask of labels for anomalies.
    mahalanobis_dist: Mahalanobis distance of reconstruction error.
    tp_thresh_var: tf.int64 variable to track number of true positives wrt
      thresholds.
    fn_thresh_var: tf.int64 variable to track number of false negatives wrt
      thresholds.
    fp_thresh_var: tf.int64 variable to track number of false positives wrt
      thresholds.
    tn_thresh_var: tf.int64 variable to track number of true negatives wrt
      thresholds.
    params: Dictionary of parameters.
    mode: Estimator ModeKeys, can take values of TRAIN and EVAL.
    anom_thresh_var: tf.float64 variable that stores anomaly threshold value.

  Returns:
    Updated variable that stores the anomaly threshold value
  """
  # shape = (num_anom_thresh,)
  anom_threshs = tf.linspace(
      start=tf.constant(
          value=params["min_{}_anom_thresh".format(var_name)],
          dtype=tf.float64),
      stop=tf.constant(
          value=params["max_{}_anom_thresh".format(var_name)],
          dtype=tf.float64),
      num=params["num_{}_anom_thresh".format(var_name)])

  with tf.variable_scope(
      name_or_scope="mahalanobis_dist_thresh_vars",
      reuse=tf.AUTO_REUSE):
    (tp_update_op,
     fn_update_op,
     fp_update_op,
     tn_update_op) = \
      update_anom_thresh_vars(
          labels_norm_mask,
          labels_anom_mask,
          params["num_{}_anom_thresh".format(var_name)],
          anom_threshs,
          mahalanobis_dist,
          tp_thresh_var,
          fn_thresh_var,
          fp_thresh_var,
          tn_thresh_var,
          mode)

  with tf.control_dependencies(
      control_inputs=[
          tp_update_op,
          fn_update_op,
          fp_update_op,
          tn_update_op]):
    _, pre, rec, f_beta = \
      calculate_composite_classification_metrics(
          tp_thresh_var,
          fn_thresh_var,
          fp_thresh_var,
          tn_thresh_var,
          params["f_score_beta"])

    with tf.control_dependencies(control_inputs=[pre, rec]):
      with tf.control_dependencies(control_inputs=[f_beta]):
        best_anom_thresh = find_best_anom_thresh(
            anom_threshs,
            f_beta,
            anom_thresh_var)
        with tf.control_dependencies(control_inputs=[best_anom_thresh]):
          return tf.identity(input=anom_thresh_var)


def set_anom_thresh(user_passed_anom_thresh, anom_thresh_var):
  """Set anomaly threshold to use for anomaly classification from user input.

  Given user passed anomaly threshold returns updated variable that stores
  the anomaly threshold value.

  Args:
    user_passed_anom_thresh: User passed anomaly threshold that overrides
      the threshold optimization.
    anom_thresh_var: tf.float64 variable that stores anomaly threshold value.

  Returns:
    Updated variable that stores the anomaly threshold value.
  """
  with tf.control_dependencies(
      control_inputs=[tf.assign(
          ref=anom_thresh_var, value=user_passed_anom_thresh)]):

    return tf.identity(input=anom_thresh_var)


def tune_anomaly_thresholds_supervised_training(
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
    dummy_var):
  """Tunes anomaly thresholds during supervised training mode.

  Given label masks, mahalanobis distances, confusion matrices, and anomaly
  thresholds, returns loss and train_op.

  Args:
    labels_norm_mask: tf.bool vector mask of labels for normals.
    labels_anom_mask: tf.bool vector mask of labels for anomalies.
    mahalanobis_dist_time: Mahalanobis distance, time major.
    tp_thresh_time_var: tf.int64 variable to track number of true positives wrt
      thresholds for time major case.
    fn_thresh_time_var: tf.int64 variable to track number of false negatives wrt
      thresholds for time major case.
    fp_thresh_time_var: tf.int64 variable to track number of false positives wrt
      thresholds for time major case.
    tn_thresh_time_var: tf.int64 variable to track number of true negatives wrt
      thresholds for time major case.
    time_anom_thresh_var: tf.float64 variable to hold the set time anomaly
      threshold.
    mahalanobis_dist_feat: Mahalanobis distance, features major.
    tp_thresh_feat_var: tf.int64 variable to track number of true positives wrt
      thresholds for feat major case.
    fn_thresh_feat_var: tf.int64 variable to track number of false negatives wrt
      thresholds for feat major case.
    fp_thresh_feat_var: tf.int64 variable to track number of false positives wrt
      thresholds for feat major case.
    tn_thresh_feat_var: tf.int64 variable to track number of true negatives wrt
      thresholds for feat major case.
    feat_anom_thresh_var: tf.float64 variable to hold the set feat anomaly
      threshold.
    params: Dictionary of parameters.
    mode: Estimator ModeKeys. Can take value of only TRAIN.
    dummy_var: Dummy variable used to allow training mode to happen since it
      requires a gradient to tie back to the graph dependency.

  Returns:
    loss: The scalar loss to tie our updates back to Estimator graph.
    train_op: The train operation to tie our updates back to Estimator graph.
  """
  # Time based
  if params["time_anom_thresh"] is None:
    best_anom_thresh_time = optimize_anomaly_theshold(
        "time",
        labels_norm_mask,
        labels_anom_mask,
        mahalanobis_dist_time,
        tp_thresh_time_var,
        fn_thresh_time_var,
        fp_thresh_time_var,
        tn_thresh_time_var,
        params,
        mode,
        time_anom_thresh_var)
  else:
    best_anom_thresh_time = set_anom_thresh(
        params["time_anom_thresh"], time_anom_thresh_var)

  # Features based
  if params["feat_anom_thresh"] is None:
    best_anom_thresh_feat = optimize_anomaly_theshold(
        "feat",
        labels_norm_mask,
        labels_anom_mask,
        mahalanobis_dist_feat,
        tp_thresh_feat_var,
        fn_thresh_feat_var,
        fp_thresh_feat_var,
        tn_thresh_feat_var,
        params,
        mode,
        feat_anom_thresh_var)
  else:
    best_anom_thresh_feat = set_anom_thresh(
        params["feat_anom_thresh"], feat_anom_thresh_var)

  with tf.control_dependencies(
      control_inputs=[best_anom_thresh_time,
                      best_anom_thresh_feat]):
    loss = tf.reduce_sum(
        input_tensor=tf.zeros(
            shape=(), dtype=tf.float64) * dummy_var)

    train_op = tf.contrib.layers.optimize_loss(
        loss=loss,
        global_step=tf.train.get_global_step(),
        learning_rate=params["learning_rate"],
        optimizer="SGD")

    return loss, train_op


def tune_anomaly_thresholds_supervised_eval(
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
    mode):
  """Checks tuned anomaly thresholds during supervised evaluation mode.

  Given label masks, mahalanobis distances, confusion matrices, and anomaly
  thresholds, returns loss and eval_metric_ops.

  Args:
    labels_norm_mask: tf.bool vector mask of labels for normals.
    labels_anom_mask: tf.bool vector mask of labels for anomalies.
    time_anom_thresh_var: tf.float64 scalar time anomaly threshold value.
    mahalanobis_dist_time: Mahalanobis distance, time major.
    tp_thresh_eval_time_var: tf.int64 variable to track number of true
      positives wrt thresholds for time major case for evaluation.
    fn_thresh_eval_time_var: tf.int64 variable to track number of false
      negatives wrt thresholds for time major case for evaluation.
    fp_thresh_eval_time_var: tf.int64 variable to track number of false
      positives wrt thresholds for time major case for evaluation.
    tn_thresh_eval_time_var: tf.int64 variable to track number of true
      negatives wrt thresholds for time major case for evaluation.
    feat_anom_thresh_var: tf.float64 scalar feature anomaly threshold value.
    mahalanobis_dist_feat: Mahalanobis distance, features major.
    tp_thresh_eval_feat_var: tf.int64 variable to track number of true
      positives wrt thresholds for feat major case for evaluation.
    fn_thresh_eval_feat_var: tf.int64 variable to track number of false
      negatives wrt thresholds for feat major case for evaluation.
    fp_thresh_eval_feat_var: tf.int64 variable to track number of false
      positives wrt thresholds for feat major case for evaluation.
    tn_thresh_eval_feat_var: tf.int64 variable to track number of true
      negatives wrt thresholds for feat major case for evaluation.
    params: Dictionary of parameters.
    mode: Estimator ModeKeys. Can take value of only EVAL.

  Returns:
    loss: Scalar reconstruction loss.
    eval_metric_ops: Evaluation metrics of threshold tuning.
  """
  with tf.variable_scope(
      name_or_scope="anom_thresh_eval_vars", reuse=tf.AUTO_REUSE):
    # Time based
    (tp_time_update_op,
     fn_time_update_op,
     fp_time_update_op,
     tn_time_update_op) = \
      update_anom_thresh_vars(
          labels_norm_mask,
          labels_anom_mask,
          1,
          time_anom_thresh_var,
          mahalanobis_dist_time,
          tp_thresh_eval_time_var,
          fn_thresh_eval_time_var,
          fp_thresh_eval_time_var,
          tn_thresh_eval_time_var,
          mode)

    # Features based
    (tp_feat_update_op,
     fn_feat_update_op,
     fp_feat_update_op,
     tn_feat_update_op) = \
      update_anom_thresh_vars(
          labels_norm_mask,
          labels_anom_mask,
          1,
          feat_anom_thresh_var,
          mahalanobis_dist_feat,
          tp_thresh_eval_feat_var,
          fn_thresh_eval_feat_var,
          fp_thresh_eval_feat_var,
          tn_thresh_eval_feat_var,
          mode)

  with tf.variable_scope(
      name_or_scope="anom_thresh_eval_vars", reuse=tf.AUTO_REUSE):
    # Time based
    (acc_time_update_op,
     pre_time_update_op,
     rec_time_update_op,
     f_beta_time_update_op) = \
      calculate_composite_classification_metrics(
          tp_thresh_eval_time_var,
          fn_thresh_eval_time_var,
          fp_thresh_eval_time_var,
          tn_thresh_eval_time_var,
          params["f_score_beta"])

    # Features based
    (acc_feat_update_op,
     pre_feat_update_op,
     rec_feat_update_op,
     f_beta_feat_update_op) = \
      calculate_composite_classification_metrics(
          tp_thresh_eval_feat_var,
          fn_thresh_eval_feat_var,
          fp_thresh_eval_feat_var,
          tn_thresh_eval_feat_var,
          params["f_score_beta"])

  loss = tf.zeros(shape=[], dtype=tf.float64)

  # Time based
  acc_trues = tf.cast(
      x=tp_thresh_eval_time_var + tn_thresh_eval_time_var,
      dtype=tf.float64)
  acc_falses = tf.cast(
      x=fp_thresh_eval_time_var + fn_thresh_eval_time_var,
      dtype=tf.float64)
  acc_thresh_eval_time_var = acc_trues / (acc_trues + acc_falses)

  tp_float = tf.cast(x=tp_thresh_eval_time_var, dtype=tf.float64)

  pre_denominator = tf.cast(
      x=tp_thresh_eval_time_var + fp_thresh_eval_time_var,
      dtype=tf.float64)
  pre_thresh_eval_time_var = tp_float / pre_denominator

  rec_denominator = tf.cast(
      x=tp_thresh_eval_time_var + fn_thresh_eval_time_var,
      dtype=tf.float64)
  rec_thresh_eval_time_var = tp_float / rec_denominator

  f_beta_numerator = (1.0 + params["f_score_beta"] ** 2)
  f_beta_numerator *= pre_thresh_eval_time_var
  f_beta_numerator *= rec_thresh_eval_time_var
  f_beta_denominator = params["f_score_beta"] ** 2
  f_beta_denominator *= pre_thresh_eval_time_var
  f_beta_denominator += rec_thresh_eval_time_var
  f_beta_thresh_eval_time_var = f_beta_numerator / f_beta_denominator

  # Features based
  acc_trues = tf.cast(
      x=tp_thresh_eval_feat_var + tn_thresh_eval_feat_var,
      dtype=tf.float64)
  acc_falses = tf.cast(
      x=fp_thresh_eval_feat_var + fn_thresh_eval_feat_var,
      dtype=tf.float64)
  acc_thresh_eval_feat_var = acc_trues / (acc_trues + acc_falses)

  tp_float = tf.cast(x=tp_thresh_eval_feat_var, dtype=tf.float64)

  pre_denominator = tf.cast(
      x=tp_thresh_eval_feat_var + fp_thresh_eval_feat_var,
      dtype=tf.float64)
  pre_thresh_eval_feat_var = tp_float / pre_denominator

  rec_denominator = tf.cast(
      x=tp_thresh_eval_feat_var + fn_thresh_eval_feat_var,
      dtype=tf.float64)
  rec_thresh_eval_feat_var = tp_float / rec_denominator

  f_beta_numerator = (1.0 + params["f_score_beta"] ** 2)
  f_beta_numerator *= pre_thresh_eval_feat_var
  f_beta_numerator *= rec_thresh_eval_feat_var
  f_beta_denominator = params["f_score_beta"] ** 2
  f_beta_denominator *= pre_thresh_eval_feat_var
  f_beta_denominator += rec_thresh_eval_feat_var
  f_beta_thresh_eval_feat_var = f_beta_numerator / f_beta_denominator

  # Anomaly detection eval metrics
  eval_metric_ops = {
      # Time based
      "time_anom_tp": (tp_thresh_eval_time_var, tp_time_update_op),
      "time_anom_fn": (fn_thresh_eval_time_var, fn_time_update_op),
      "time_anom_fp": (fp_thresh_eval_time_var, fp_time_update_op),
      "time_anom_tn": (tn_thresh_eval_time_var, tn_time_update_op),

      "time_anom_acc": (acc_thresh_eval_time_var, acc_time_update_op),
      "time_anom_pre": (pre_thresh_eval_time_var, pre_time_update_op),
      "time_anom_rec": (rec_thresh_eval_time_var, rec_time_update_op),
      "time_anom_f_beta": (f_beta_thresh_eval_time_var,
                           f_beta_time_update_op),

      # Features based
      "feat_anom_tp": (tp_thresh_eval_feat_var, tp_feat_update_op),
      "feat_anom_fn": (fn_thresh_eval_feat_var, fn_feat_update_op),
      "feat_anom_fp": (fp_thresh_eval_feat_var, fp_feat_update_op),
      "feat_anom_tn": (tn_thresh_eval_feat_var, tn_feat_update_op),

      "feat_anom_acc": (acc_thresh_eval_feat_var, acc_feat_update_op),
      "feat_anom_pre": (pre_thresh_eval_feat_var, pre_feat_update_op),
      "feat_anom_rec": (rec_thresh_eval_feat_var, rec_feat_update_op),
      "feat_anom_f_beta": (f_beta_thresh_eval_feat_var,
                           f_beta_feat_update_op)
  }

  return loss, eval_metric_ops
