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

def linear_model(img, mode):
  X = tf.reshape(img, [-1, HEIGHT*WIDTH]) # flattened
  #W = tf.Variable(tf.zeros([HEIGHT*WIDTH, NCLASSES]))
  #b = tf.Variable(tf.zeros([NCLASSES]))
  W = tf.Variable(tf.truncated_normal([HEIGHT*WIDTH, NCLASSES], stddev=0.1))
  b = tf.Variable(tf.truncated_normal([NCLASSES], stddev=0.1))
  ylogits = tf.matmul(X, W) + b
  return ylogits, NCLASSES

def dnn_model(img, mode):
  X = tf.reshape(img, [-1, HEIGHT*WIDTH]) # flattened
  h1 = tf.layers.dense(X, 300, activation=tf.nn.relu)
  h2 = tf.layers.dense(h1,100, activation=tf.nn.relu)
  h3 = tf.layers.dense(h2, 30, activation=tf.nn.relu)
  ylogits = tf.layers.dense(h3, NCLASSES, activation=None)
  return ylogits, NCLASSES

MODELS = {
  'linear' : linear_model,
  'dnn' : dnn_model
}
def get_model_names() :
  return MODELS.keys()
def get_model_func(name) :
  return MODELS[name]

def serving_input_fn():
    inputs = {'image': tf.placeholder(tf.float32, [None, HEIGHT, WIDTH])}
    features = inputs # as-is
    return tf.estimator.export.ServingInputReceiver(features, inputs)

