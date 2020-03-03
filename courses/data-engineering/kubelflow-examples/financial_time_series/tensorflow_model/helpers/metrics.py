"""Module that defines metrics that are evaluated when training the model.

Uses tensor operations to construct the confusion matrix for validation of predictions.
"""
import tensorflow as tf

def tf_calc_confusion_matrix_ops(actuals, predictions):
  """Constructs the Tensorflow operations for obtaining the confusion matrix operators.

  Args:
    actuals (tf.tensor): tensor that contain actuals
    predictions (tf.tensor): tensor that contains predictions

  Returns:
    tensors: true_postive, true_negative, false_positive, false_negative

  """

  ones_like_actuals = tf.ones_like(actuals)
  zeros_like_actuals = tf.zeros_like(actuals)
  ones_like_predictions = tf.ones_like(predictions)
  zeros_like_predictions = tf.zeros_like(predictions)

  tp_op = tf.reduce_sum(
      tf.cast(
          tf.logical_and(
              tf.equal(actuals, ones_like_actuals),
              tf.equal(predictions, ones_like_predictions)
          ),
          "float"
      )
  )

  tn_op = tf.reduce_sum(
      tf.cast(
          tf.logical_and(
              tf.equal(actuals, zeros_like_actuals),
              tf.equal(predictions, zeros_like_predictions)
          ),
          "float"
      )
  )

  fp_op = tf.reduce_sum(
      tf.cast(
          tf.logical_and(
              tf.equal(actuals, zeros_like_actuals),
              tf.equal(predictions, ones_like_predictions)
          ),
          "float"
      )
  )

  fn_op = tf.reduce_sum(
      tf.cast(
          tf.logical_and(
              tf.equal(actuals, ones_like_actuals),
              tf.equal(predictions, zeros_like_predictions)
          ),
          "float"
      )
  )

  return tp_op, tn_op, fp_op, fn_op


def tf_calc_confusion_metrics(true_pos, true_neg, false_pos, false_neg):
  """Construct the Tensorflow operations for obtaining the confusion matrix.

  Args:
    true_pos (tf.tensor): tensor with true positives
    true_neg (tf.tensor): tensor with true negatives
    false_pos (tf.tensor): tensor with false positives
    false_neg (tf.tensor): tensor with false negatives

  Returns:
    tensor calculations: precision, recall, f1_score and accuracy

  """
  tpfn = float(true_pos) + float(false_neg)
  tpr = 0 if tpfn == 0 else float(true_pos) / tpfn

  total = float(true_pos) + float(false_pos) + float(false_neg) + float(true_neg)
  accuracy = 0 if total == 0 else (float(true_pos) + float(true_neg)) / total

  recall = tpr
  tpfp = float(true_pos) + float(false_pos)
  precision = 0 if tpfp == 0 else float(true_pos) / tpfp

  f1_score = 0 if recall == 0 else (2 * (precision * recall)) / (precision + recall)

  print('Precision = ', precision)
  print('Recall = ', recall)
  print('F1 Score = ', f1_score)
  print('Accuracy = ', accuracy)

  return {'precision': precision, 'recall': recall, 'f1': f1_score,
          'accuracy': accuracy}


def tf_confusion_matrix(model, actual_classes, session, feed_dict):
  """Calculates confusion matrix when training.

  Args:
    model (object): instance of the model class Object
    actual_classes (tf.tensor): tensor that contains the actual classes
    session (tf.session): tensorflow session in which the tensors are evaluated
    feed_dict (dict): dictionary with features and actual classes


  """

  predictions = tf.argmax(model, 1)
  actuals = tf.argmax(actual_classes, 1)
  tp_op, tn_op, fp_op, fn_op = tf_calc_confusion_matrix_ops(actuals, predictions)
  true_pos, true_neg, false_pos, false_neg = \
      session.run(
          [tp_op, tn_op, fp_op, fn_op],
          feed_dict
      )

  return tf_calc_confusion_metrics(true_pos, true_neg, false_pos, false_neg)
