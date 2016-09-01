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
import setup
import subprocess
import sys
import time

import tensorflow as tf


from tensorflow.python.platform import gfile
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


flags = tf.app.flags
FLAGS = flags.FLAGS
flags.DEFINE_float('learning_rate', .001, 'Initial learning rate.')
flags.DEFINE_integer('max_steps', 100000, 'Number of steps to run trainer.')
flags.DEFINE_integer('batch_size', 10, 'Batch size - Must divide evenly into the dataset sizes.')
flags.DEFINE_string('input_dir', 'input', 'Directory where training, validation, and test data is located')
flags.DEFINE_string('output_path', 'output', 'Directory to which output is written')
flags.DEFINE_string('training_data_file', 'train-taxi.csv', 'File containing training data')
flags.DEFINE_string('validation_data_file', 'validation-taxi.csv', 'File containing validation data')
flags.DEFINE_string('test_data_file', 'test-taxi.csv', 'File containing test data')
flags.DEFINE_boolean('train_on_cloud', False, 'True if model should be trained in cloud')

DISCOVERY_URL = ('https://storage.googleapis.com/cloud-ml/discovery/ml_v1alpha3_discovery.json')
NUM_EXAMPLES = 1000
NUM_FEATURES = 1
NUM_OUTPUTS = 1
MODEL_NAME = 'taxi_regression'
TAR_FILE = '{package}-{version}.tar.gz'.format(package=setup.NAME, version=setup.VERSION)

Dataset = collections.namedtuple('Dataset', ['data', 'target'])
Datasets = collections.namedtuple('Datasets', ['train', 'validation', 'test'])


def main():
  job_name = MODEL_NAME + '_' + datetime.datetime.now().strftime('%y%m%d_%H%M%S')
  job = {
      'job_name': job_name,
      'module_name': 'PACKAGE' + '.' + 'MODULE',
  }
  if FLAGS.train_on_cloud:
    train_on_cloud(job)
  else:
    train_locally(job_name)

def perform_preprocessing(examples):
  # TODO(bgb): Implement any necessary preprocessing.
  pass

def read_tf_format(filename_queue):
  reader = tf.TFRecordReader()
  _, value = reader.read(filename_queue)
  feature_map = {
    'trip_distance': tf.FixedLenFeature([1], dtype=tf.float_, default_value=0.0),
    'fare_amount': tf.FixedLenFeature([1], dtype=tf.float_, default_value=0.0),
  }
  example = tf.parse_single_example(value, feature_map)
  features = features['trip_distance']
  label = features['fare_amount']
  return features, label


def read_csv_format(filename_queue):
  reader = tf.TextLineReader()
  _, value = reader.read(filename_queue)
  record_defaults = [[0.0], [0.0]]
  # Extracting into columns before packing into example and label in case of larger feature/label set in future.
  col1, col2 = tf.decode_csv(
      value, record_defaults=record_defaults)
  example = tf.pack([col1])
  label = tf.pack([col2])
  return example, label

def input_pipeline_multiple_readers():
  filename_queue = tf.train.string_input_producer(["input/train-taxi.csv", "input/train-taxi2.csv"], shuffle=False)
  read_threads = 2 #Do not set this to be greater than the length of the filename queue.

  example_list = [read_csv_format(filename_queue) for _ in range(read_threads)]
  min_after_dequeue = 10000
  capacity = (read_threads + 1) * min_after_dequeue * FLAGS.batch_size # Must be > batch size and < size of memory.
  example_batch, label_batch = tf.train.shuffle_batch_join(
      example_list, batch_size=FLAGS.batch_size, capacity=capacity, min_after_dequeue=min_after_dequeue)
  return example_batch, label_batch

def input_pipeline_single_reader():
  filename_queue = tf.train.string_input_producer(["input/train-taxi.csv", "input/train-taxi2.csv"], shuffle=False)
  example, label = read_csv_format(filename_queue)
  min_after_dequeue = 10000
  capacity = 2 * min_after_dequeue * FLAGS.batch_size # Must be > batch size and < size of memory.
  example_batch, label_batch = tf.train.shuffle_batch(
      [example, label], batch_size=FLAGS.batch_size, capacity=capacity)  #, min_after_dequeue=min_after_dequeue)
  return example_batch, label_batch

def train_locally(job_name):
  print 'Output will be written to: %s' % job_name

  with tf.Graph().as_default():
    examples_batch, labels_batch = input_pipeline_multiple_readers()
    processed_examples = perform_preprocessing(examples_batch)
    W = tf.Variable(tf.zeros([NUM_OUTPUTS, NUM_FEATURES]))
    b = tf.Variable(tf.zeros([NUM_OUTPUTS]))
    y = tf.transpose(tf.matmul(W, tf.transpose(examples_batch)) + b)
    loss = tf.reduce_sum(tf.square(tf.sub(labels_batch, y)))/(2*FLAGS.batch_size)
    train_op = tf.train.GradientDescentOptimizer(FLAGS.learning_rate).minimize(loss)


    init = tf.initialize_all_variables()
    sess = tf.Session()
    sess.run(init)


    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)

    for step in range(FLAGS.max_steps):
      _, loss_value, weights, bias, examples, labels = sess.run([train_op, loss, W, b, examples_batch, labels_batch])

      if step % 100 == 0:
        #print('Step %d: loss = %.2f. Current weights: %s Bias: %s.' % (step, loss_value, weights, bias))
        print('Examples: %s. Labels: %s' % (examples, labels))
        print("Labels: %s" % (labels_batch))
        #print("Predicted labels: %s" % (y))
        #print '\n'

    # TODO(bgb): Evaluate model using validation and test sets. Write output to appropriate file.


def train_on_cloud(job):
  tar_src = _create_tarball()
  tar_dest = os.path.join(FLAGS.output_path, TAR_FILE)
  copy = ['gsutil', 'cp', tar_src, tar_dest]
  subprocess.check_call(copy)

  credentials = GoogleCredentials.get_application_default()
  api = discovery.build('ml', 'v1alpha3', credentials=credentials, discoveryServiceUrl=DISCOVERY_URL)

  job.update({
      'master_spec': {'replica_count': 1},
  })

  # TODO(bgb): Get project.
  params_json = json.dumps(job, indent=2)
  #response = api.projects().submitTrainingJob(body=job, parent='projects/' + project).execute()
  print 'Submitting training job %s' % (job['job_name'],)
  logging.info('api.projects().submitTrainingJob(**%s)', params_json)


def _create_tarball():
  sdist = ['python', 'setup.py', 'sdist', '--format=gztar']
  with open('/dev/null', 'w') as dev_null:
    subprocess.check_call(sdist, stdout=dev_null, stderr=dev_null)
  return os.path.join('dist', TAR_FILE)


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
