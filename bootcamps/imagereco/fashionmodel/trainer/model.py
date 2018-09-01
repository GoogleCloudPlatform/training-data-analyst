#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
tf.logging.set_verbosity(tf.logging.INFO)

HEIGHT=28
WIDTH=28
NCLASSES=10

def linear_model(img, mode, hparams):
  X = tf.reshape(img,[-1,HEIGHT*WIDTH]) #flatten
  ylogits = tf.layers.dense(X,NCLASSES,activation=None)
  return ylogits, NCLASSES

def dnn_model(img, mode, hparams):
  X = tf.reshape(img, [-1, HEIGHT*WIDTH]) #flatten
  h1 = tf.layers.dense(X, 300, activation=tf.nn.relu)
  h2 = tf.layers.dense(h1,100, activation=tf.nn.relu)
  h3 = tf.layers.dense(h2, 30, activation=tf.nn.relu)
  ylogits = tf.layers.dense(h3, NCLASSES, activation=None)
  return ylogits, NCLASSES

def dnn_dropout_model(img, mode, hparams):
  dprob = hparams.get('dprob', 0.1)

  X = tf.reshape(img, [-1, HEIGHT*WIDTH]) #flatten
  h1 = tf.layers.dense(X, 300, activation=tf.nn.relu)
  h2 = tf.layers.dense(h1,100, activation=tf.nn.relu)
  h3 = tf.layers.dense(h2, 30, activation=tf.nn.relu)
  h3d = tf.layers.dropout(h3, rate=dprob, training=(
      mode == tf.estimator.ModeKeys.TRAIN)) #only dropout when training
  ylogits = tf.layers.dense(h3d, NCLASSES, activation=None)
  return ylogits, NCLASSES

def cnn_model(img, mode, hparams):
  ksize1 = hparams.get('ksize1', 5)
  ksize2 = hparams.get('ksize2', 5)
  nfil1 = hparams.get('nfil1', 10)
  nfil2 = hparams.get('nfil2', 20)
  dprob = hparams.get('dprob', 0.25)
  
  c1 = tf.layers.conv2d(img, filters=nfil1,
                          kernel_size=ksize1, strides=1, # ?x28x28x10
                          padding='same', activation=tf.nn.relu)
  p1 = tf.layers.max_pooling2d(c1,pool_size=2, strides=2) # ?x14x14x10
  c2 = tf.layers.conv2d(p1, filters=nfil2,
                          kernel_size=ksize2, strides=1, 
                          padding='same', activation=tf.nn.relu)
  p2 = tf.layers.max_pooling2d(c2,pool_size=2, strides=2) # ?x7x7x20
  
  outlen = p2.shape[1]*p2.shape[2]*p2.shape[3] #980
  p2flat = tf.reshape(p2, [-1, outlen]) # flattened

  #apply batch normalization
  if hparams['batch_norm']:
    h3 = tf.layers.dense(p2flat, 300, activation=None)
    h3 = tf.layers.batch_normalization(
        h3, training=(mode == tf.estimator.ModeKeys.TRAIN)) #only batchnorm when training
    h3 = tf.nn.relu(h3)
  else:  
    h3 = tf.layers.dense(p2flat, 300, activation=tf.nn.relu)
  
  #apply dropout
  h3d = tf.layers.dropout(h3, rate=dprob, training=(mode == tf.estimator.ModeKeys.TRAIN))

  ylogits = tf.layers.dense(h3d, NCLASSES, activation=None)
  
  #apply batch normalization once more
  if hparams['batch_norm']:
     ylogits = tf.layers.batch_normalization(
         ylogits, training=(mode == tf.estimator.ModeKeys.TRAIN))

  return ylogits, NCLASSES

def serving_input_fn():
    #input will be rank 3
    feature_placeholders = {
        'image': tf.placeholder(tf.float32, [None, HEIGHT, WIDTH])}
    #but model function requires rank 4
    features = {
        'image': tf.expand_dims(feature_placeholders['image'],-1)} 
    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)

def image_classifier(features, labels, mode, params):
  model_functions = {
      'linear':linear_model,
      'dnn':dnn_model,
      'dnn_dropout':dnn_dropout_model,
      'cnn':cnn_model}
  model_function = model_functions[params['model']]  
  ylogits, nclasses = model_function(features['image'], mode, params)

  probabilities = tf.nn.softmax(ylogits)
  classes = tf.cast(tf.argmax(probabilities, 1), tf.uint8)
  if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
    loss = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits_v2(
            logits=ylogits, labels=labels))
    evalmetrics = {'accuracy': tf.metrics.accuracy(classes, tf.argmax(labels, 1))}
    if mode == tf.estimator.ModeKeys.TRAIN:
      # this is needed for batch normalization, but has no effect otherwise
      update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
      with tf.control_dependencies(update_ops):
         train_op = tf.contrib.layers.optimize_loss(
             loss, 
             tf.train.get_global_step(),
             learning_rate=params['learning_rate'], 
             optimizer="Adam")
    else:
      train_op = None
  else:
    loss = None
    train_op = None
    evalmetrics = None
 
  return tf.estimator.EstimatorSpec(
        mode=mode,
        predictions={"probabilities": probabilities, "classes": classes},
        loss=loss,
        train_op=train_op,
        eval_metric_ops=evalmetrics,
        export_outputs={'classes':tf.estimator.export.PredictOutput(
            {"probabilities": probabilities, "classes": classes})}
    )

def train_and_evaluate(output_dir, hparams):
  EVAL_INTERVAL = 60

  mnist = input_data.read_data_sets('mnist/data', one_hot=True, reshape=False)

  train_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={'image':mnist.train.images},
    y=mnist.train.labels,
    batch_size=100,
    num_epochs=None,
    shuffle=True,
    queue_capacity=5000
  )

  eval_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={'image':mnist.test.images},
    y=mnist.test.labels,
    batch_size=100,
    num_epochs=1,
    shuffle=False,
    queue_capacity=5000
  )
  estimator = tf.estimator.Estimator(model_fn = image_classifier,
                                     params = hparams,
                                     config=tf.estimator.RunConfig(
                                         save_checkpoints_secs = EVAL_INTERVAL),
                                     model_dir = output_dir)
  train_spec = tf.estimator.TrainSpec(input_fn = train_input_fn,
                                    max_steps = hparams['train_steps'])
  exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)
  eval_spec = tf.estimator.EvalSpec(input_fn = eval_input_fn,
                                  steps = None,
                                  exporters = exporter,
                                  throttle_secs = EVAL_INTERVAL)
  tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)