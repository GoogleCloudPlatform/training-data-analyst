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

tf.logging.set_verbosity(tf.logging.INFO)

HEIGHT=28
WIDTH=28
NCLASSES=10

def linear_model(img, mode, hparams):
  X = tf.reshape(img,[-1,HEIGHT*WIDTH]) #flatten
  W = tf.get_variable("W", [HEIGHT*WIDTH,NCLASSES], 
                      initializer = tf.truncated_normal_initializer(stddev=0.1,seed = 1))
  b = tf.get_variable("b",NCLASSES, initializer = tf.zeros_initializer)
  ylogits = tf.matmul(X,W)+b
  return ylogits, NCLASSES

def dnn_model(img, mode, hparams):
  X = tf.reshape(img, [-1, HEIGHT*WIDTH]) # flattened
  h1 = tf.layers.dense(X, 300, activation=tf.nn.relu)
  h2 = tf.layers.dense(h1,100, activation=tf.nn.relu)
  h3 = tf.layers.dense(h2, 30, activation=tf.nn.relu)
  ylogits = tf.layers.dense(h3, NCLASSES, activation=None)
  return ylogits, NCLASSES

def dnn_dropout_model(img, mode, hparams):
  X = tf.reshape(img, [-1, HEIGHT*WIDTH]) # flattened
  h1 = tf.layers.dense(X, 300, activation=tf.nn.relu)
  h2 = tf.layers.dense(h1,100, activation=tf.nn.relu)
  h3 = tf.layers.dense(h2, 30, activation=tf.nn.relu)
  h3d = tf.layers.dropout(h3, rate=0.1, training=(mode == tf.estimator.ModeKeys.TRAIN))
  ylogits = tf.layers.dense(h3d, NCLASSES, activation=None)
  return ylogits, NCLASSES

def cnn_model(img, mode, hparams):
  ksize1 = hparams.get('ksize1', 5)
  ksize2 = hparams.get('ksize2', 5)
  nfil1 = hparams.get('nfil1', 10)
  nfil2 = hparams.get('nfil2', 20)
  dprob = hparams.get('dprob', 0.25)

  X = tf.reshape(img, [-1, HEIGHT, WIDTH, 1]) # as a 2D image with one grayscale channel
  c1 = tf.layers.max_pooling2d(
         tf.layers.conv2d(X, filters=nfil1,
                          kernel_size=ksize1, strides=1, # ?x28x28x10
                          padding='same', activation=tf.nn.relu),
         pool_size=2, strides=2
       ) # ?x14x14x10
  c2 = tf.layers.max_pooling2d(
         tf.layers.conv2d(c1, filters=nfil2,
                          kernel_size=ksize2, strides=1, 
                          padding='same', activation=tf.nn.relu),
         pool_size=2, strides=2
       ) # ?x7x7x20

  outlen = (HEIGHT//4)*(WIDTH//4)*nfil2 # integer division; 980
  c2flat = tf.reshape(c2, [-1, outlen]) # flattened

  if hparams['batch_norm']:
    h3 = tf.layers.dense(c2flat, 300, activation=None)
    h3 = tf.layers.batch_normalization(h3, training=(mode == tf.estimator.ModeKeys.TRAIN))
    h3 = tf.nn.relu(h3)
  else:  
    h3 = tf.layers.dense(c2flat, 300, activation=tf.nn.relu)

  h3d = tf.layers.dropout(h3, rate=dprob, training=(mode == tf.estimator.ModeKeys.TRAIN))

  ylogits = tf.layers.dense(h3d, NCLASSES, activation=None)

  if hparams['batch_norm']:
     ylogits = tf.layers.batch_normalization(ylogits, training=(mode == tf.estimator.ModeKeys.TRAIN))

  return ylogits, NCLASSES

def serving_input_fn():
    inputs = {'image': tf.placeholder(tf.float32, [None, HEIGHT, WIDTH])}
    features = inputs # as-is
    return tf.estimator.export.ServingInputReceiver(features, inputs)

