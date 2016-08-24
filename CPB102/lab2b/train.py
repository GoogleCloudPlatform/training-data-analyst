"""A script for launching the model training script.

The code that is run is mnist/task.py.

During the typical development cycle, one will often start by training
models locally using a subset of the data to ensure things are working
as expected. Then, one can try distributed training locally to ensure
everything works correctly for distributed training. Finally, training
on the full data is performed in the cloud. For example:

  # Train locally, in a single process.
  python train.py

  # Train in the cloud
  python train.py --output_path=gs://my_bucket/out --cloud
"""

import argparse
import collections
import csv
import datetime
import json
import logging
import numpy as np
import os
import subprocess
import sys
import time

import tensorflow as tf

from tensorflow.python.platform import gfile


flags = tf.app.flags
FLAGS = flags.FLAGS
flags.DEFINE_float('learning_rate', .001, 'Initial learning rate.')
flags.DEFINE_integer('max_steps', 10000, 'Number of steps to run trainer.')
flags.DEFINE_integer('batch_size', 100, 'Batch size - Must divide evenly into the dataset sizes.')
flags.DEFINE_string('input_dir', 'input', 'Directory where training, validation, and test data is located')
flags.DEFINE_string('output_path', 'output', 'Directory to which output is written')
flags.DEFINE_string('training_data_file', 'train-taxi.csv', 'File containing training data')
flags.DEFINE_string('validation_data_file', 'validation-taxi.csv', 'File containing validation data')
flags.DEFINE_string('test_data_file', 'test-taxi.csv', 'File containing test data')

NUM_EXAMPLES = 1000
NUM_FEATURES = 1
NUM_OUTPUTS = 1
MODEL_NAME = 'taxi_regression'

Dataset = collections.namedtuple('Dataset', ['data', 'target'])
Datasets = collections.namedtuple('Datasets', ['train', 'validation', 'test'])


def main():
  job_name = MODEL_NAME + '_' + datetime.datetime.now().strftime('%y%m%d_%H%M%S')
  train_locally(job_name)


def train_locally(job_name):
  print 'Output will be written to: %s' % job_name

  train = _load_csv_without_header(os.path.join(FLAGS.input_dir, FLAGS.training_data_file), target_dtype=np.float_, features_dtype=np.float_,target_column=1)
  validation = _load_csv_without_header(os.path.join(FLAGS.input_dir, FLAGS.validation_data_file), target_dtype=np.float_, features_dtype=np.float_,target_column=1)
  test = _load_csv_without_header(os.path.join(FLAGS.input_dir, FLAGS.test_data_file), target_dtype=np.float_, features_dtype=np.float_,target_column=1)
  data_sets = Datasets(train=train, validation=validation, test=test)

  with tf.Graph().as_default():
    training_placeholder = tf.placeholder(tf.float32, shape=(FLAGS.batch_size, NUM_FEATURES))
    labels_placeholder = tf.placeholder(tf.float32, shape=(FLAGS.batch_size))
    W = tf.Variable(tf.zeros([NUM_OUTPUTS, NUM_FEATURES]))
    b = tf.Variable(tf.zeros([NUM_OUTPUTS]))
    y = tf.matmul(W, tf.transpose(training_placeholder)) + b
    loss = tf.reduce_sum(tf.square(tf.sub(labels_placeholder, y)))/(2*FLAGS.batch_size)
    train_op = tf.train.GradientDescentOptimizer(FLAGS.learning_rate).minimize(loss)

    init = tf.initialize_all_variables()
    sess = tf.Session()
    sess.run(init)

    for step in range(FLAGS.max_steps):
      batch_start_index = (step * FLAGS.batch_size) % NUM_EXAMPLES
      training_feed = data_sets.train.data[batch_start_index:batch_start_index+FLAGS.batch_size]
      labels_feed = data_sets.train.target[batch_start_index:batch_start_index+FLAGS.batch_size]
      feed_dict = {
          training_placeholder: training_feed,
          labels_placeholder: labels_feed,
      }

      _, loss_value, weights, bias = sess.run([train_op, loss, W, b], feed_dict=feed_dict)

      if step % 1000 == 0:
        print('Step %d: loss = %.2f. Current weights: %s Bias: %s.' % (step, loss_value, weights, bias))

    # TODO(bgb): Evaluate model using validation and test sets. Write output to appropriate file.


def _load_csv_without_header(filename,
                            target_dtype,
                            features_dtype,
                            target_column=-1):
  with gfile.Open(filename) as csv_file:
    data_file = csv.reader(csv_file)
    data, target = [], []
    for row in data_file:
      target.append(row.pop(target_column))
      data.append(np.asarray(row, dtype=features_dtype))

  target = np.array(target, dtype=target_dtype)
  data = np.array(data)
  return Dataset(data=np.array(data),
                 target=np.array(target).astype(target_dtype))



if __name__ == '__main__':
  main()
