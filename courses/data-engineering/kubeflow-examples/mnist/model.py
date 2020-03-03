#  Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""This showcases how simple it is to build image classification networks.

It follows description from this TensorFlow tutorial:
    https://www.tensorflow.org/versions/master/tutorials/mnist/pros/index.html#deep-mnist-for-experts
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import os
import sys
import numpy as np
import tensorflow as tf

N_DIGITS = 10  # Number of digits.
X_FEATURE = 'x'  # Name of the input feature.


def parse_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument('--tf-data-dir',
                      type=str,
                      default='/tmp/data/',
                      help='GCS path or local path of training data.')
  parser.add_argument('--tf-model-dir',
                      type=str,
                      help='GCS path or local directory.')
  parser.add_argument('--tf-export-dir',
                      type=str,
                      default='mnist/',
                      help='GCS path or local directory to export model')
  parser.add_argument('--tf-model-type',
                      type=str,
                      default='CNN',
                      help='Tensorflow model type for training.')
  parser.add_argument('--tf-train-steps',
                      type=int,
                      default=200,
                      help='The number of training steps to perform.')
  parser.add_argument('--tf-batch-size',
                      type=int,
                      default=100,
                      help='The number of batch size during training')
  parser.add_argument('--tf-learning-rate',
                      type=float,
                      default=0.01,
                      help='Learning rate for training.')

  args = parser.parse_known_args()[0]
  return args


def conv_model(features, labels, mode, params):
  """2-layer convolution model."""
  # Reshape feature to 4d tensor with 2nd and 3rd dimensions being
  # image width and height final dimension being the number of color channels.
  feature = tf.reshape(features[X_FEATURE], [-1, 28, 28, 1])

  # First conv layer will compute 32 features for each 5x5 patch
  with tf.variable_scope('conv_layer1'):
    h_conv1 = tf.layers.conv2d(
        feature,
        filters=32,
        kernel_size=[5, 5],
        padding='same',
        activation=tf.nn.relu)
    h_pool1 = tf.layers.max_pooling2d(
        h_conv1, pool_size=2, strides=2, padding='same')

  # Second conv layer will compute 64 features for each 5x5 patch.
  with tf.variable_scope('conv_layer2'):
    h_conv2 = tf.layers.conv2d(
        h_pool1,
        filters=64,
        kernel_size=[5, 5],
        padding='same',
        activation=tf.nn.relu)
    h_pool2 = tf.layers.max_pooling2d(
        h_conv2, pool_size=2, strides=2, padding='same')
    # reshape tensor into a batch of vectors
    h_pool2_flat = tf.reshape(h_pool2, [-1, 7 * 7 * 64])

  # Densely connected layer with 1024 neurons.
  h_fc1 = tf.layers.dense(h_pool2_flat, 1024, activation=tf.nn.relu)
  h_fc1 = tf.layers.dropout(
      h_fc1,
      rate=0.5,
      training=(mode == tf.estimator.ModeKeys.TRAIN))

  # Compute logits (1 per class) and compute loss.
  logits = tf.layers.dense(h_fc1, N_DIGITS, activation=None)
  predict = tf.nn.softmax(logits)
  classes = tf.cast(tf.argmax(predict, 1), tf.uint8)

  # Compute predictions.
  predicted_classes = tf.argmax(logits, 1)
  if mode == tf.estimator.ModeKeys.PREDICT:
    predictions = {
        'class': predicted_classes,
        'prob': tf.nn.softmax(logits)
    }
    return tf.estimator.EstimatorSpec(mode, predictions=predictions,
        export_outputs={'classes':
                        tf.estimator.export.PredictOutput({"predictions": predict,
                                                           "classes": classes})})

  # Compute loss.
  loss = tf.losses.sparse_softmax_cross_entropy(labels=labels, logits=logits)

  # Create training op.
  if mode == tf.estimator.ModeKeys.TRAIN:
    optimizer = tf.train.GradientDescentOptimizer(
        learning_rate=params["learning_rate"])
    train_op = optimizer.minimize(loss, global_step=tf.train.get_global_step())
    return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)

  # Compute evaluation metrics.
  eval_metric_ops = {
      'accuracy': tf.metrics.accuracy(
          labels=labels, predictions=predicted_classes)
  }
  return tf.estimator.EstimatorSpec(
      mode, loss=loss, eval_metric_ops=eval_metric_ops)


def cnn_serving_input_receiver_fn():
  inputs = {X_FEATURE: tf.placeholder(tf.float32, [None, 28, 28])}
  return tf.estimator.export.ServingInputReceiver(inputs, inputs)


def linear_serving_input_receiver_fn():
  inputs = {X_FEATURE: tf.placeholder(tf.float32, (784,))}
  return tf.estimator.export.ServingInputReceiver(inputs, inputs)


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)

  args = parse_arguments()

  tf_config = os.environ.get('TF_CONFIG', '{}')
  tf.logging.info("TF_CONFIG %s", tf_config)
  tf_config_json = json.loads(tf_config)
  cluster = tf_config_json.get('cluster')
  job_name = tf_config_json.get('task', {}).get('type')
  task_index = tf_config_json.get('task', {}).get('index')
  tf.logging.info("cluster=%s job_name=%s task_index=%s", cluster, job_name,
                  task_index)

  is_chief = False
  if not job_name or job_name.lower() in ["chief", "master"]:
    is_chief = True
    tf.logging.info("Will export model")
  else:
    tf.logging.info("Will not export model")

  # Download and load MNIST dataset.
  mnist = tf.contrib.learn.datasets.DATASETS['mnist'](args.tf_data_dir)
  train_input_fn = tf.estimator.inputs.numpy_input_fn(
      x={X_FEATURE: mnist.train.images},
      y=mnist.train.labels.astype(np.int32),
      batch_size=args.tf_batch_size,
      num_epochs=None,
      shuffle=True)
  test_input_fn = tf.estimator.inputs.numpy_input_fn(
      x={X_FEATURE: mnist.train.images},
      y=mnist.train.labels.astype(np.int32),
      num_epochs=1,
      shuffle=False)

  training_config = tf.estimator.RunConfig(
      model_dir=args.tf_model_dir, save_summary_steps=100, save_checkpoints_steps=1000)

  if args.tf_model_type == "LINEAR":
    # Linear classifier.
    feature_columns = [
        tf.feature_column.numeric_column(
            X_FEATURE, shape=mnist.train.images.shape[1:])]
    classifier = tf.estimator.LinearClassifier(
        feature_columns=feature_columns, n_classes=N_DIGITS,
        model_dir=args.tf_model_dir, config=training_config)
    # TODO(jlewi): Should it be linear_serving_input_receiver_fn here?
    serving_fn = cnn_serving_input_receiver_fn
    export_final = tf.estimator.FinalExporter(
        args.tf_export_dir, serving_input_receiver_fn=cnn_serving_input_receiver_fn)

  elif args.tf_model_type == "CNN":
    # Convolutional network
    model_params = {"learning_rate": args.tf_learning_rate}
    classifier = tf.estimator.Estimator(
        model_fn=conv_model, model_dir=args.tf_model_dir,
        config=training_config, params=model_params)
    serving_fn = cnn_serving_input_receiver_fn
    export_final = tf.estimator.FinalExporter(
        args.tf_export_dir, serving_input_receiver_fn=cnn_serving_input_receiver_fn)
  else:
    print("No such model type: %s" % args.tf_model_type)
    sys.exit(1)

  train_spec = tf.estimator.TrainSpec(
        input_fn=train_input_fn, max_steps=args.tf_train_steps)
  eval_spec = tf.estimator.EvalSpec(input_fn=test_input_fn,
                                      steps=1,
                                      exporters=export_final,
                                      throttle_secs=1,
                                      start_delay_secs=1)
  print("Train and evaluate")
  tf.estimator.train_and_evaluate(classifier, train_spec, eval_spec)
  print("Training done")

  if is_chief:
    print("Export saved model")
    classifier.export_savedmodel(args.tf_export_dir, serving_input_receiver_fn=serving_fn)
    print("Done exporting the model")

if __name__ == '__main__':
  tf.app.run()
