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

LIST_OF_LABELS = 'daisy,dandelion,roses,sunflowers,tulips'.split(',')
HEIGHT = 299
WIDTH = 299
NUM_CHANNELS = 3
NCLASSES = 5

def linear_model(img, mode, hparams):
  nvalues = HEIGHT*WIDTH*NUM_CHANNELS
  X = tf.reshape(img, [-1, nvalues]) # flattened
  W = tf.Variable(tf.truncated_normal([nvalues, NCLASSES], stddev=0.1))
  b = tf.Variable(tf.truncated_normal([NCLASSES], stddev=0.1))
  ylogits = tf.matmul(X, W) + b
  return ylogits, NCLASSES

def dnn_model(img, mode, hparams):
  X = tf.reshape(img, [-1, HEIGHT*WIDTH*NUM_CHANNELS]) # flattened
  h1 = tf.layers.dense(X, 300, activation=tf.nn.relu)
  h2 = tf.layers.dense(h1,100, activation=tf.nn.relu)
  h3 = tf.layers.dense(h2, 30, activation=tf.nn.relu)
  ylogits = tf.layers.dense(h3, NCLASSES, activation=None)
  return ylogits, NCLASSES

def dnn_dropout_model(img, mode, hparams):
  X = tf.reshape(img, [-1, HEIGHT*WIDTH*NUM_CHANNELS]) # flattened
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

  X = tf.reshape(img, [-1, HEIGHT, WIDTH, NUM_CHANNELS]) # as a 2D image
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

def read_and_preprocess(filename, augment=False):
    # decode the image file starting from the filename
    # end up with pixel values that are in the -1, 1 range
    image_contents = tf.read_file(filename)
    image = tf.image.decode_jpeg(image_contents, channels=NUM_CHANNELS)
    image = tf.image.convert_image_dtype(image, dtype=tf.float32) # 0-1
    image = tf.expand_dims(image, 0) # resize_bilinear needs batches

    if augment:
       image = tf.image.resize_bilinear(image, [HEIGHT+10, WIDTH+10], align_corners=False)
       image = tf.random_crop(image, [HEIGHT, WIDTH, NUM_CHANNELS])
       image = tf.random_flip_left_right(image)
       image = tf.image.random_brightness(image, max_delta=63.0/255.0)
       image = tf.image.random_contrast(image, lower=0.2, upper=1.8)
    else:
       image = tf.image.resize_bilinear(image, [HEIGHT, WIDTH], align_corners=False)

    tf.logging.info('After resizing ... image={}'.format(image.get_shape()))
    #image = tf.image.per_image_whitening(image)  # useful if mean not important
    image = tf.subtract(image, 0.5)
    image = tf.multiply(image, 2.0) # -1 to 1
    return image

def serving_input_fn():
    # Note: only handles one image at a time ... 
    inputs = {'imageurl': tf.placeholder(tf.string, shape=())}
    filename = tf.squeeze(inputs['imageurl']) # make it a scalar
    image = read_and_preprocess(filename)
    # make the outer dimension unknown (and not 1)
    image = tf.placeholder_with_default(image, shape=[None, HEIGHT, WIDTH, NUM_CHANNELS])

    features = {'image' : image}
    return tf.estimator.export.ServingInputReceiver(features, inputs)
