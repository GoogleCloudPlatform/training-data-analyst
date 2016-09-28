#!/usr/bin/env python
# Copyright 2016 Google Inc. All Rights Reserved.
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

import math
import multiprocessing

import tensorflow as tf

import google.cloud.ml.features as features


# This reads TF records after preprocessing. Nothing to change here
def read_examples(input_files, batch_size, shuffle, num_epochs=None):
  thread_count = multiprocessing.cpu_count()

  # The minimum number of instances in a queue from which examples are drawn
  # randomly. The larger this number, the more randomness at the expense of
  # higher memory requirements.
  MIN_AFTER_DEQUEUE = 100

  # When batching data, the queue's capacity will be larger than the batch_size
  # by some factor. The recommended formula is (num_threads + a small safety
  # margin). For now, we use a single thread for reading, so this can be small.
  QUEUE_SIZE_MULTIPLIER = thread_count + 3

  # Convert num_epochs == 0 -> num_epochs is None, if necessary
  num_epochs = num_epochs or None

  # input_files could be a path to one file or a file pattern.
  input_file_names = tf.train.match_filenames_once(input_files)

  # Build a queue of the filenames to be read.
  filename_queue = tf.train.string_input_producer(input_file_names, num_epochs,
                                                  shuffle)
  options = tf.python_io.TFRecordOptions(
      compression_type=tf.python_io.TFRecordCompressionType.GZIP)
  example_id, encoded_example = tf.TFRecordReader(options=options).read_up_to(
      filename_queue, batch_size)

  if shuffle:
    capacity = MIN_AFTER_DEQUEUE + QUEUE_SIZE_MULTIPLIER * batch_size
    return tf.train.shuffle_batch([example_id, encoded_example], batch_size,
                                  capacity, MIN_AFTER_DEQUEUE,
                                  enqueue_many=True, num_threads=thread_count)
  else:
    capacity = QUEUE_SIZE_MULTIPLIER * batch_size
    return tf.train.batch([example_id, encoded_example],
                          batch_size, capacity=capacity,
                          enqueue_many=True, num_threads=thread_count)


def _print_shape(t, name):
  if t == None or t.get_shape() == None:
     print name, ' = None'
  else:
     print name, ' = ', t.get_shape().as_list()

# TODO: make hyperparameter
NUMBUCKETS = 5

def feature_cross_latlon(plat, plon, name):
    # discretize plat. numbers are in [-1,1] so if you want 11 buckets, need to multiply by 5 to get [-5,5]
    scalefactor = tf.constant((NUMBUCKETS - 1) / 2.0)
    dplat = tf.round( tf.scalar_mul(scalefactor, plat) , name='discretize_{0}_latitude'.format(name) )
    dplon = tf.round( tf.scalar_mul(scalefactor, plon) , name='discretize_{0}_longitude'.format(name) )

    # FC dplat x dplon
    depth = NUMBUCKETS * NUMBUCKETS
    dplatlon_index = tf.to_int32(tf.round(tf.add(tf.scalar_mul(tf.constant(NUMBUCKETS*1.0), dplat), dplon)), name='{0}_location_index'.format(name))
    dplatlon = tf.squeeze(tf.one_hot(dplatlon_index, depth, axis=-1, name='{0}_location'.format(name)), [1])  # (batchsize, 1, depth) -> batchsize, depth
    return dplatlon_index, dplatlon


def _create_fakekey(input_data):
   batchsize = tf.shape(input_data)[0]
   return tf.ones([batchsize], dtype=tf.float32)


# TaxiFeatures is a dictionary; pull Tensors from the dictionary, and create features
def create_inputs(metadata, input_data=None):
  with tf.name_scope('inputs'):
    if input_data is None:
      input_data = tf.placeholder(tf.string, name='input', shape=(None,))
    parsed = features.FeatureMetadata.parse_features(metadata, input_data)

    # [batchsize, 1] 
    plat = parsed['plat']
    plon = parsed['plon']
    dlat = parsed['dlat']
    dlon = parsed['dlon']
    dayofweek = parsed['dayofweek']
    hourofday = parsed['hourofday']

    # pickup is [batchsize, nbuckets**2]
    pickup_index, pickup = feature_cross_latlon(plat, plon, 'pickup')
    dropoff_index, dropoff = feature_cross_latlon(dlat, dlon, 'dropoff')
    # pickupdropoff is [batchsize, nbuckets**4]
    pickupdropoff = tf.squeeze(tf.one_hot(tf.mul(pickup_index, dropoff_index), depth=NUMBUCKETS**4, axis=-1), [1])
    latdist = tf.abs(tf.sub(plat, dlat))
    londist = tf.abs(tf.sub(plon, dlon))

    _print_shape(plat, 'plat')
    _print_shape(latdist, 'latdist')
    _print_shape(pickup, 'pickup')
    _print_shape(pickupdropoff, 'pickupdropoff')

    # weekend/weekday, rush-hours and low-traffic nighttime
    weekend = tf.to_float(tf.logical_or( tf.greater(dayofweek, 6.5), tf.less(dayofweek, 1.5), name='weekend')) #Sa,Su
    night = tf.to_float(tf.logical_or( tf.greater(hourofday, 21.5), tf.less(hourofday, 6.5), name='night')) #10-6
    morning = tf.to_float(tf.logical_or( tf.greater(hourofday, 6.5), tf.less(hourofday, 10.5), name='morning')) #7-10
    evening = tf.to_float(tf.logical_or( tf.greater(hourofday, 15.5), tf.less(hourofday, 20.5), name='evening')) #4-8

    # combine all the inputs
    inputs = tf.concat(1, [plat, plon, dlat, dlon, latdist, londist, pickup, dropoff, pickupdropoff, weekend, night, morning, evening])
    print 'inputs=',inputs.get_shape().as_list()

    return (input_data, inputs, tf.squeeze(parsed['fare_amount']),
            _create_fakekey(input_data)) # no key tf.identity(parsed['key']))

def inference(inputs, metadata, hyperparams):
  # input_size = metadata.features['inputs']['size']
  input_size = 6 + (NUMBUCKETS**2) * 2 + (NUMBUCKETS**4) + 4
  output_size = metadata.features['fare_amount']['size']

  h = [hyperparams['hidden_layer1_size'],
       hyperparams['hidden_layer2_size'],
       hyperparams['hidden_layer3_size']]
  hidden = tf.contrib.layers.stack(inputs,
                                   tf.contrib.layers.fully_connected,
                                   h, activation_fn=tf.nn.relu)
  output = tf.contrib.layers.fully_connected(hidden, output_size, activation_fn=None)
  output = tf.identity(output, 'predicted_fare') # assign name

  return output


def loss(output, targets):
  """Calculates the loss from the output and the labels.
  Args:
    output: output layer tensor, float - [batch_size].
    targets: Target value tensor, float - [batch_size].
  Returns:
    loss_op: Loss tensor of type float.
  """
  loss = tf.sqrt(tf.reduce_mean(tf.square(output - targets)), name = 'loss') # RMSE
  return loss

def training(loss_op, learning_rate):
  with tf.name_scope('train'):
    tf.scalar_summary(loss_op.op.name, loss_op)
    global_step = tf.Variable(0, name='global_step', trainable=False)
    optimizer = tf.train.AdagradOptimizer(learning_rate)
    train_op = optimizer.minimize(loss_op, global_step)
    return train_op, global_step
