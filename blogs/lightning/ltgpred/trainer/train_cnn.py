#!/usr/bin/env python
"""Train model to predict lightning using a simple convnet.

Copyright Google Inc.
2018 Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required
by applicable law or agreed to in writing, software distributed under the
License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.
"""
from __future__ import division
from __future__ import print_function
import argparse
import functools
import logging
import os
import time
import tensorflow as tf


def reshape_into_image(features, params):
  """reshape features dict containing ref, ltg channels into image.

  Args:
    features (dict): Looks for ref, ltg entries in dict
    params (dict): command-line parameters

  Returns:
    reshaped tensor with shape [2*predsize, 2*predsize, 2]
  """
  # stack the inputs to form a 2-channel input
  # features['ref'] is [-1, height*width]
  # stacked image is [-1, height*width, n_channels]
  n_channels = 2
  print('shape of ref feature {}'.format(features['ref'].shape))
  stacked = tf.concat([features['ref'], features['ltg']], axis=1)
  # See create_dataset.py: cy - boxdef.N:cy + boxdef.N
  height = 2 * params['predsize']
  width = 2 * params['predsize']
  print('shape of all features {}, will be reshaped to [{},{},{}]'.format(
      stacked.shape, height, width, n_channels))
  return tf.reshape(stacked, [height, width, n_channels])


def make_preprocess_fn(params):
  """Make preprocessing function.

  Args:
    params (dict): command-line parameters

  Returns:
    function that takes tfexample and returns img, label
  """
  def _sparse_to_dense(data, arrlen):
    return tf.expand_dims(
        tf.reshape(tf.sparse_tensor_to_dense(data, default_value=0), [arrlen]),
        -1)

  def read_and_preprocess(example_data):
    """parses tfrecord and returns image, label.

    Args:
      example_data (str): tfrecord
    Returns:
      img, label
    """
    # See create_dataset.py: cy - boxdef.N:cy + boxdef.N
    height = 2 * params['predsize']
    width = 2 * params['predsize']
    parsed = tf.parse_single_example(
        example_data, {
            'ref': tf.VarLenFeature(tf.float32),
            'ltg': tf.VarLenFeature(tf.float32),
            'has_ltg': tf.FixedLenFeature([], tf.int64, 1),
        })
    parsed['ref'] = _sparse_to_dense(parsed['ref'], height * width)
    parsed['ltg'] = _sparse_to_dense(parsed['ltg'], height * width)
    label = tf.cast(tf.reshape(parsed['has_ltg'], shape=[]), dtype=tf.int32)
    print('shape of label {}'.format(label.shape))

    img = reshape_into_image(parsed, params)
    return img, label

  return read_and_preprocess


def _convnet(img, mode, params):
  """Neural network layers for simple convnet model.

  Args:
    img (tensor): image tensor
    mode (int): TRAIN, EVAL or PREDICT
    params (dict): command-line parameters

  Returns:
    logits
  """
  # hyperparams
  ksize = params.get('ksize', 5)
  nfil = params.get('nfil', 10)
  nlayers = params.get('nlayers', 3)
  dprob = params.get('dprob', 0.05 if params['batch_norm'] else 0.25)

  # conv net with batchnorm
  convout = img
  xavier = tf.contrib.layers.xavier_initializer(seed=13)
  for layer in range(nlayers):
    # convolution
    c1 = tf.layers.conv2d(
        convout,
        filters=nfil,
        kernel_size=ksize,
        kernel_initializer=xavier,
        strides=1,
        padding='same',
        activation=tf.nn.relu)
    # maxpool
    convout = tf.layers.max_pooling2d(c1, pool_size=2, strides=2, padding='same')
    print('Shape of output of {}th layer = {} {}'.format(
        layer + 1, convout.shape, convout))

  print('Shape of conv layers output = {}'.format(convout.shape))
  outlen = convout.shape[1] * convout.shape[2] * convout.shape[3]
  p2flat = tf.reshape(convout, [-1, outlen])  # flattened

  # apply batch normalization
  if params['batch_norm']:
    h3 = tf.layers.dense(
        p2flat, 100, activation=None, kernel_initializer=xavier)
    h3 = tf.layers.batch_normalization(
        h3, training=(mode == tf.estimator.ModeKeys.TRAIN
                     ))  # only batchnorm when training
    h3 = tf.nn.relu(h3)
  else:
    h3 = tf.layers.dense(
        p2flat, 100, activation=tf.nn.relu, kernel_initializer=xavier)

  # apply dropout
  h3d = tf.layers.dropout(
      h3, rate=dprob, training=(mode == tf.estimator.ModeKeys.TRAIN))

  ylogits = tf.layers.dense(h3d, 1, activation=None)
  return ylogits


def convnet_ltg(features, labels, mode, params):
  """Model function for a simple convnet.

  Args:
    features (dict): features
    labels (tensor): labels
    mode (int): TRAIN, EVAL or PREDICT
    params (dict): command-line parameters

  Returns:
    tpuestimatorspec
  """
  # comes in directly during training, wrapped in dict during serving
  image = features['image'] if isinstance(features, dict) else features

  # do convolutional layers
  ylogits = _convnet(image, mode, params)

  # output layer from logits
  ltgprob = tf.nn.sigmoid(ylogits)
  class_int = tf.round(ltgprob)

  if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
    print('shape of ylogits={}'.format(ylogits))
    loss = tf.reduce_mean(
        tf.nn.sigmoid_cross_entropy_with_logits(
            logits=tf.reshape(ylogits, [-1]),
            labels=tf.cast(labels, dtype=tf.float32)))

    def metric_fn(labels, class_int, ltgprob):
      return {
          'accuracy':
              tf.metrics.accuracy(labels, class_int),
          'rmse':
              tf.metrics.root_mean_squared_error(
                  tf.cast(labels, dtype=tf.float32), ltgprob)
      }

    evalmetrics = (metric_fn, [labels, class_int, ltgprob])

    if mode == tf.estimator.ModeKeys.TRAIN:
      # this is needed for batch normalization, but has no effect otherwise
      update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
      optimizer = tf.train.GradientDescentOptimizer(
          learning_rate=params['learning_rate'])
      if params['use_tpu']:
        optimizer = tf.contrib.tpu.CrossShardOptimizer(optimizer)  # for TPU
      with tf.control_dependencies(update_ops):
        train_op = optimizer.minimize(loss, tf.train.get_global_step())
    else:
      train_op = None
  else:
    loss = None
    train_op = None
    evalmetrics = None

  return tf.contrib.tpu.TPUEstimatorSpec(  # works on TPU, GPU, CPU
      mode=mode,
      predictions={
          'ltg_probability': ltgprob,
          'has_ltg': class_int
      },
      loss=loss,
      train_op=train_op,
      eval_metrics=evalmetrics,
      export_outputs={
          'ltgpred':
              tf.estimator.export.PredictOutput({
                  'ltg_probability': ltgprob,
                  'has_ltg': class_int
              })
      })


def load_global_step_from_checkpoint_dir(checkpoint_dir):
  try:
    checkpoint_reader = tf.train.NewCheckpointReader(
        tf.train.latest_checkpoint(checkpoint_dir))
    return checkpoint_reader.get_tensor(tf.GraphKeys.GLOBAL_STEP)
  except:  # pylint: disable=bare-except
    return 0


def make_serving_input_fn(params):
  """Make serving input function.

  Args:
    params (dict): command-line parameters

  Returns:
    serving input function suitable for exporting
  """
  def serving_input_fn():  # pylint: disable=missing-docstring
    # Note: only handles one image at a time
    boxsize = 4 * params['predsize'] * params['predsize']
    feature_placeholders = {
        'ref': tf.placeholder(tf.float32, shape=[None, boxsize]),
        'ltg': tf.placeholder(tf.float32, shape=[None, boxsize])
    }

    # add an extra dim for batchsize and create image tensor
    print('Shape of serving input ref = {}'.format(
        feature_placeholders['ref'].shape))
    features = {
        key: tf.expand_dims(tf.reshape(tensor, [boxsize]), -1)
        for key, tensor in feature_placeholders.items()
    }
    image = reshape_into_image(features, params)
    image = tf.expand_dims(image, 0)  # [-1, 2*N, 2*N, 2]
    print('Shape of image input = {}'.format(image.shape))

    return tf.estimator.export.ServingInputReceiver({
        'image': image
    }, feature_placeholders)

  return serving_input_fn


def make_input_fn(pattern, mode, num_cores, transpose_input):
  """Make training/evaluation input function.

  Args:
    pattern (str): filename pattern
    mode (int): TRAIN/EVAL/PREDICT
    num_cores (int): If training on TPU, the number of cores to use
    transpose_input (bool): more efficient training on TPU

  Returns:
    input function suitable for sending to estimator
  """
  def _set_shapes(batch_size, images, labels):
    """Statically set the batch_size dimension."""
    if transpose_input:
      images.set_shape(images.get_shape().merge_with(
          tf.TensorShape([None, None, None, batch_size])))
      labels.set_shape(labels.get_shape().merge_with(
          tf.TensorShape([batch_size])))
    else:
      images.set_shape(images.get_shape().merge_with(
          tf.TensorShape([batch_size, None, None, None])))
      labels.set_shape(labels.get_shape().merge_with(
          tf.TensorShape([batch_size])))
    return images, labels

  def _input_fn(params):  # pylint: disable=missing-docstring
    batch_size = params['batch_size']  # provided by TPU
    is_training = (mode == tf.estimator.ModeKeys.TRAIN)

    # read the dataset
    dataset = tf.data.Dataset.list_files(pattern, shuffle=is_training)
    if is_training:
      dataset = dataset.repeat()

    def fetch_dataset(filename):
      buffer_size = 8 * 1024 * 1024  # 8 MiB per file
      dataset = tf.data.TFRecordDataset(filename, buffer_size=buffer_size)
      return dataset

    dataset = dataset.apply(
        tf.contrib.data.parallel_interleave(
            fetch_dataset, cycle_length=64, sloppy=True))
    dataset = dataset.shuffle(1024)

    # convert features into images
    preprocess_fn = make_preprocess_fn(params)
    dataset = dataset.apply(
        tf.contrib.data.map_and_batch(
            preprocess_fn,
            batch_size=batch_size,
            num_parallel_batches=num_cores,
            drop_remainder=True))

    if transpose_input:
      dataset = dataset.map(
          lambda images, labels: (tf.transpose(images, [1, 2, 3, 0]), labels),
          num_parallel_calls=num_cores)

    # assign static shape
    dataset = dataset.map(functools.partial(_set_shapes, batch_size))

    # prefetch data while training
    dataset = dataset.prefetch(tf.contrib.data.AUTOTUNE)
    return dataset

  return _input_fn


def train_and_evaluate(hparams):
  """Main train and evaluate loop.

  Args:
    hparams (dict): Command-line parameters passed in
  """
  output_dir = hparams['job_dir']
  STEPS_PER_EVAL = 1000  # pylint: disable=invalid-name
  max_steps = hparams['train_steps']
  # eval batch size has to be divisible by num_cores
  eval_batch_size = min(hparams['num_eval_records'],
                        hparams['train_batch_size'])
  eval_batch_size = eval_batch_size - eval_batch_size % hparams['num_cores']
  tf.logging.info('train_batch_size=%d  eval_batch_size=%d  max_steps=%d',
                  hparams['train_batch_size'], eval_batch_size, max_steps)

  # resolve TPU if necessary
  if hparams['use_tpu']:
    tpu_cluster_resolver = tf.contrib.cluster_resolver.TPUClusterResolver(
        hparams['tpu'], zone=hparams['tpu_zone'], project=hparams['project'])
    config = tf.contrib.tpu.RunConfig(
        cluster=tpu_cluster_resolver,
        model_dir=output_dir,
        save_checkpoints_steps=STEPS_PER_EVAL,
        tpu_config=tf.contrib.tpu.TPUConfig(
            iterations_per_loop=STEPS_PER_EVAL,
            per_host_input_for_training=True))
  else:
    config = tf.contrib.tpu.RunConfig()

  estimator = tf.contrib.tpu.TPUEstimator(  # TPU change 4
      model_fn=convnet_ltg,
      config=config,
      params=hparams,
      model_dir=output_dir,
      train_batch_size=hparams['train_batch_size'],
      eval_batch_size=eval_batch_size,
      use_tpu=hparams['use_tpu'])

  # set up training and evaluation in a loop
  train_input_fn = make_input_fn(hparams['train_data_path'],
                                 tf.estimator.ModeKeys.TRAIN,
                                 hparams['num_cores'], hparams['transpose'])
  eval_input_fn = make_input_fn(hparams['eval_data_path'],
                                tf.estimator.ModeKeys.EVAL,
                                hparams['num_cores'], hparams['transpose'])

  # load last checkpoint and start from there
  current_step = load_global_step_from_checkpoint_dir(output_dir)
  tf.logging.info('Training for %d steps. Current step %d.', max_steps,
                  current_step)

  start_timestamp = time.time()  # This time will include compilation time

  while current_step < hparams['train_steps']:
    # Train for up to steps_per_eval number of steps.
    # At the end of training, a checkpoint will be written to --model_dir.
    next_checkpoint = min(current_step + STEPS_PER_EVAL, max_steps)
    estimator.train(input_fn=train_input_fn, max_steps=next_checkpoint)
    current_step = next_checkpoint
    tf.logging.info('Finished training up to step %d. Elapsed seconds %d.',
                    next_checkpoint, int(time.time() - start_timestamp))

    # Evaluate the model on the most recent model in --model_dir.
    # Since evaluation happens in batches of --eval_batch_size, some images
    # may be excluded modulo the batch size. As long as the batch size is
    # consistent, the evaluated images are also consistent.
    tf.logging.info('Starting to evaluate at step %d', next_checkpoint)
    eval_results = estimator.evaluate(
        input_fn=eval_input_fn,
        steps=hparams['num_eval_records'] // eval_batch_size)
    tf.logging.info('Eval results at step %d: %s', next_checkpoint,
                    eval_results)

  elapsed_time = int(time.time() - start_timestamp)
  tf.logging.info('Finished training up to step %d. Elapsed seconds %d.',
                  max_steps, elapsed_time)

  # export similar to Cloud ML Engine convention
  tf.logging.info('Starting to export model.')
  estimator.export_savedmodel(
      export_dir_base=os.path.join(output_dir, 'export/exporter'),
      serving_input_receiver_fn=make_serving_input_fn(hparams))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Train cnn model for lightning prediction')
  parser.add_argument(
      '--job-dir', required=True, help='output dir. could be local or on GCS')
  parser.add_argument(
      '--train_data_path',
      required=True,
      help='Pattern for training data tfrecord files. could be local or on GCS')
  parser.add_argument(
      '--eval_data_path',
      required=True,
      help='Pattern for evaluation data tfrecord files.'
      'could be local or on GCS'
  )
  parser.add_argument(
      '--predsize',
      type=int,
      default=32,
      help='predict lightning within a NxN grid; has to match preprocessing')
  parser.add_argument(
      '--train_batch_size',
      help='Batch size for training steps',
      type=int,
      default=256)
  parser.add_argument(
      '--learning_rate',
      help='Initial learning rate for training',
      type=float,
      default=1e-6)
  parser.add_argument(
      '--train_steps',
      help="""\
        Steps to run the training job for. A step is one batch-size,\
        """,
      type=int,
      default=100)
  parser.add_argument(
      '--num_eval_records',
      help='Number of validation records, '
      ' has to be less than available number and'
      ' divisible by number of cores.'
      ' You can find available number from Dataflow'
      ' pipeline that created the tfrecords dataset'
      ' See: https://console.cloud.google.com/dataflow',
      type=int,
      default=128)

  # for Cloud TPU
  parser.add_argument(
      '--use_tpu',
      help=
      ('If specified, use TPU to execute the model for training and evaluation.'
       ' Else use whatever devices are available to'
       ' TensorFlow by default (e.g. CPU and GPU)'),
      dest='use_tpu',
      action='store_true')
  parser.add_argument(
      '--transpose',
      help=('If specified, makes the batch-size the last dimension.'
            ' This is more efficient on a TPU'),
      dest='transpose',
      action='store_true')
  parser.add_argument(
      '--tpu',
      default=None,
      help='The Cloud TPU to use for training. This should be either the name '
      'used when creating the Cloud TPU, or grpc://ip.address.of.tpu:8470 url.'
  )
  parser.add_argument(
      '--project',
      default=None,
      help='Project name for the Cloud TPU-enabled project. If not specified, '
      'will attempt to automatically detect the GCE project from metadata.')
  parser.add_argument(
      '--tpu_zone',
      default=None,
      help='GCE zone where the Cloud TPU is located in. If not specified, we '
      'will attempt to automatically detect the GCE project from metadata.')
  parser.add_argument(
      '--num_cores', default=8, type=int, help='Number of TPU cores to use')

  # optional hyperparameters used by cnn
  parser.add_argument(
      '--ksize', help='kernel size of each layer for CNN', type=int, default=5)
  parser.add_argument(
      '--nfil',
      help='number of filters in each layer for CNN',
      type=int,
      default=10)
  parser.add_argument(
      '--nlayers', help='number of layers in CNN (<= 5)', type=int, default=3)
  parser.add_argument(
      '--dprob', help='dropout probability for CNN', type=float, default=0.25)
  parser.add_argument(
      '--batch_norm',
      help='if specified, do batch_norm for CNN',
      dest='batch_norm',
      action='store_true')

  logging.basicConfig(level=getattr(logging, 'INFO', None))
  parser.set_defaults(use_tpu=False, batch_norm=False)
  options = parser.parse_args().__dict__

  # run the training job
  train_and_evaluate(options)
