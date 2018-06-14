#!/usr/bin/env python

# Copyright 2018 Google Inc. All Rights Reserved.
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

import tensorflow as tf
import numpy as np

from functools import partial

from tensorflow.examples.tutorials.mnist import input_data

# Set logging to be level of INFO
tf.logging.set_verbosity(tf.logging.INFO)

# read data

mnist = input_data.read_data_sets('MNIST_data', one_hot=True)

# define model layers

he_init = tf.keras.initializers.he_normal()

def build_fully_connected(X, n_units=100, activation=tf.keras.activations.relu, initialization=he_init,
                          batch_normalization=False, training=False, name=None):
    layer = tf.keras.layers.Dense(n_units,
                                  activation=None,
                                  kernel_initializer=he_init,
                                  name=name)(X)
    if batch_normalization:
        bn = tf.keras.layers.BatchNormalization(momentum=0.90)
        layer = bn(layer, training=training)
    return activation(layer)

def output_layer(h, n_units, initialization=he_init,
                 batch_normalization=False, training=False):
    logits = tf.keras.layers.Dense(n_units, activation=None)(h)
    if batch_normalization:
        bn = tf.keras.layers.BatchNormalization(momentum=0.90)
        logits = bn(logits, training=training)
    return logits

# build model

ACTIVATION = tf.keras.activations.relu
BATCH_SIZE = 550
HIDDEN_UNITS = [500,400,300,200,100,50,25]
LEARNING_RATE = 0.01
NUM_STEPS = 10
USE_BATCH_NORMALIZATION = False


def dnn_custom_estimator(features, labels, mode, params):
    in_training = mode == tf.estimator.ModeKeys.TRAIN
    use_batch_norm = params['batch_norm']
    
    net = tf.feature_column.input_layer(features, params['features'])
    for i, n_units in enumerate(params['hidden_units']):
        net = build_fully_connected(net, n_units=n_units, training=in_training, 
                                    batch_normalization=use_batch_norm, 
                                    activation=params['activation'],
                                    name='hidden_layer'+str(i))
    
    logits = output_layer(net, 10, batch_normalization=use_batch_norm,
                          training=in_training)
    
    predicted_classes = tf.argmax(logits, 1)
    loss = tf.losses.softmax_cross_entropy(onehot_labels=labels, logits=logits)
    accuracy = tf.metrics.accuracy(labels=tf.argmax(labels, 1),
                                   predictions=predicted_classes,
                                   name='acc_op')
    tf.summary.scalar('accuracy', accuracy[1])  # for visualizing in TensorBoard
    if mode == tf.estimator.ModeKeys.EVAL:
        return tf.estimator.EstimatorSpec(mode, loss=loss,
                                          eval_metric_ops={'accuracy': accuracy})

    # Create training op.
    assert mode == tf.estimator.ModeKeys.TRAIN

    extra_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
    optimizer = tf.train.AdamOptimizer(learning_rate=params['learning_rate'])
    with tf.control_dependencies(extra_ops):
        train_op = optimizer.minimize(loss, global_step=tf.train.get_global_step())

    return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)    

# set up estimator

def read_mnist(X, y, num_epochs=None, batch_size=550, shuffle=False):
    feature_dict = {'image_data': X}
    return tf.estimator.inputs.numpy_input_fn(x=feature_dict, y=y.astype(np.int32),
                                              num_epochs=num_epochs,
                                              batch_size=batch_size,
                                              shuffle=shuffle)


train_input_fn = read_mnist(mnist.train.images, mnist.train.labels,
                            num_epochs=None, batch_size=BATCH_SIZE,
                            shuffle=True)

eval_input_fn = read_mnist(mnist.test.images, mnist.test.labels,
                           num_epochs=1, batch_size=BATCH_SIZE,
                           shuffle=False)

def train_and_evaluate(output_dir):
    print(HIDDEN_UNITS)
    features = [tf.feature_column.numeric_column(key='image_data', shape=(28*28))]
    classifier = tf.estimator.Estimator(model_fn=dnn_custom_estimator,
                                        model_dir=output_dir,
                                        params={'features': features,
                                                'batch_norm': USE_BATCH_NORMALIZATION,
                                                'activation': ACTIVATION,
                                                'hidden_units': HIDDEN_UNITS,
                                                'learning_rate': LEARNING_RATE})

    train_spec = tf.estimator.TrainSpec(input_fn=train_input_fn, max_steps=NUM_STEPS)
    eval_spec = tf.estimator.EvalSpec(input_fn=eval_input_fn,
                                      throttle_secs=10  # evaluate every N seconds
                                     )
    tf.estimator.train_and_evaluate(classifier, train_spec, eval_spec)
