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

import functools
import os
import time

import tensorflow as tf

tf.logging.set_verbosity(tf.logging.INFO)

LIST_OF_LABELS = 'daisy,dandelion,roses,sunflowers,tulips'.split(',')
HEIGHT = 299
WIDTH = 299
NUM_CHANNELS = 3
NCLASSES = 5

def cnn_model(img, mode, hparams):
  ksize1 = hparams.get('ksize1', 5)
  ksize2 = hparams.get('ksize2', 5)
  nfil1 = hparams.get('nfil1', 10)
  nfil2 = hparams.get('nfil2', 20)
  dprob = hparams.get('dprob', 0.25)
  
  c1 = tf.layers.conv2d(img, filters=nfil1,
                          kernel_size=ksize1, strides=1, 
                          padding='same', activation=tf.nn.relu)
  p1 = tf.layers.max_pooling2d(c1,pool_size=2, strides=2) 
  c2 = tf.layers.conv2d(p1, filters=nfil2,
                          kernel_size=ksize2, strides=1, 
                          padding='same', activation=tf.nn.relu)
  p2 = tf.layers.max_pooling2d(c2,pool_size=2, strides=2)
  
  outlen = p2.shape[1]*p2.shape[2]*p2.shape[3] 
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
    
def read_and_preprocess(example_data):
    parsed = tf.parse_single_example(example_data, {
      'image/encoded': tf.FixedLenFeature((), tf.string, ''),
      'image/class/label': tf.FixedLenFeature([], tf.int64, 1),
    })
    image_bytes = tf.reshape(parsed['image/encoded'], shape=[])
    label = tf.cast(
      tf.reshape(parsed['image/class/label'], shape=[]), dtype=tf.int32) - 1

    # end up with pixel values that are in the -1, 1 range
    image = tf.image.decode_jpeg(image_bytes, channels=NUM_CHANNELS)
    image = tf.image.convert_image_dtype(image, dtype=tf.float32) # 0-1
    image = tf.expand_dims(image, 0) # resize_bilinear needs batches

    image = tf.image.resize_bilinear(
      image, [HEIGHT + 10, WIDTH + 10], align_corners=False)
    image = tf.squeeze(image)  # remove batch dimension
    image = tf.random_crop(image, [HEIGHT, WIDTH, NUM_CHANNELS])
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, max_delta=63.0 / 255.0)
    image = tf.image.random_contrast(image, lower=0.2, upper=1.8)

        
    #pixel values are in range [0,1], convert to [-1,1]
    image = tf.subtract(image, 0.5)
    image = tf.multiply(image, 2.0)
    #return {'image':image}, label
    return image, label

def serving_input_fn():
    # Note: only handles one image at a time 
    feature_placeholders = {'image_bytes': 
                            tf.placeholder(tf.string, shape=())}
    image, _ = read_and_preprocess(
        tf.squeeze(feature_placeholders['image_bytes']))
    features = {
      'image': tf.expand_dims(image, 0)
    }
    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)

def make_input_fn(pattern, mode, num_cores=8, transpose_input=False):
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

  def _input_fn(params):
    batch_size = params['batch_size']
    is_training = (mode == tf.estimator.ModeKeys.TRAIN)

    # read the dataset
    dataset = tf.data.Dataset.list_files(pattern, shuffle=is_training)
    if is_training:
      dataset = dataset.repeat()
    def fetch_dataset(filename):
      buffer_size = 8 * 1024 * 1024 # 8 MiB per file
      dataset = tf.data.TFRecordDataset(filename, buffer_size=buffer_size)
      return dataset
    dataset = dataset.apply(
      tf.contrib.data.parallel_interleave(
        fetch_dataset, cycle_length=64, sloppy=True))
    dataset = dataset.shuffle(1024)

    # augment and batch
    dataset = dataset.apply(
      tf.contrib.data.map_and_batch(
        read_and_preprocess, batch_size=batch_size,
        num_parallel_batches=num_cores, drop_remainder=True
    ))

    if transpose_input:
      dataset = dataset.map(
        lambda images, labels: (tf.transpose(images, [1, 2, 3, 0]), labels),
        num_parallel_calls=num_cores)

    # assign static shape
    dataset = dataset.map(
      functools.partial(_set_shapes, batch_size)
    )

    # prefetch data while training
    dataset = dataset.prefetch(tf.contrib.data.AUTOTUNE)
    return dataset

  return _input_fn
    
def image_classifier(features, labels, mode, params):
  image = features
  if isinstance(features, dict):
    image = features['image']

  ylogits, nclasses = cnn_model(image, mode, params)

  probabilities = tf.nn.softmax(ylogits)
  class_int = tf.cast(tf.argmax(probabilities, 1), tf.int32)
  class_str = tf.gather(LIST_OF_LABELS, class_int)
  
  if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(
        logits=ylogits, labels=tf.one_hot(labels, nclasses)))

    def metric_fn(class_int, labels):
      return {'accuracy': tf.metrics.accuracy(class_int, labels)}
    evalmetrics = (metric_fn, [class_int, labels])

    if mode == tf.estimator.ModeKeys.TRAIN:
      # this is needed for batch normalization, but has no effect otherwise
      update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
      optimizer = tf.train.AdamOptimizer(learning_rate=params['learning_rate'])
      if params['use_tpu']:
        optimizer = tf.contrib.tpu.CrossShardOptimizer(optimizer) # TPU change 1
      with tf.control_dependencies(update_ops):
         train_op = optimizer.minimize(loss, tf.train.get_global_step())
    else:
      train_op = None
  else:
    loss = None
    train_op = None
    evalmetrics = None

  return tf.contrib.tpu.TPUEstimatorSpec(  # TPU change 2
        mode=mode,
        predictions={"probabilities": probabilities, 
                     "classid": class_int, "class": class_str},
        loss=loss,
        train_op=train_op,
        eval_metrics=evalmetrics,
        export_outputs={'classes': tf.estimator.export.PredictOutput(
            {"probabilities": probabilities, "classid": class_int, 
             "class": class_str})}
    )

def load_global_step_from_checkpoint_dir(checkpoint_dir):
  try:
    checkpoint_reader = tf.train.NewCheckpointReader(
        tf.train.latest_checkpoint(checkpoint_dir))
    return checkpoint_reader.get_tensor(tf.GraphKeys.GLOBAL_STEP)
  except:  # pylint: disable=bare-except
    return 0

def train_and_evaluate(output_dir, hparams):
  STEPS_PER_EVAL = 1000
  max_steps = hparams['train_steps']
  eval_batch_size = min(1024, hparams['num_eval_images'])
  eval_batch_size = eval_batch_size - eval_batch_size % 8  # divisible by num_cores
  tf.logging.info('train_batch_size=%d  eval_batch_size=%d  max_steps=%d',
                  hparams['train_batch_size'],
                  eval_batch_size,
                  max_steps)

  # TPU change 3
  if hparams['use_tpu']:
    tpu_cluster_resolver = tf.contrib.cluster_resolver.TPUClusterResolver(
      hparams['tpu'],
      zone=hparams['tpu_zone'],
      project=hparams['project'])
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
    model_fn=image_classifier,
    config=config,
    params=hparams,
    model_dir=output_dir,
    train_batch_size=hparams['train_batch_size'],
    eval_batch_size=eval_batch_size,
    use_tpu=hparams['use_tpu']
  )

  # set up training and evaluation in a loop
  train_input_fn = make_input_fn(hparams['train_data_path'],
                                 mode=tf.estimator.ModeKeys.TRAIN)
  eval_input_fn = make_input_fn(hparams['eval_data_path'],
                                mode=tf.estimator.ModeKeys.EVAL)

  # load last checkpoint and start from there
  current_step = load_global_step_from_checkpoint_dir(output_dir)
  steps_per_epoch = hparams['num_train_images'] // hparams['train_batch_size']
  tf.logging.info('Training for %d steps (%.2f epochs in total). Current'
                  ' step %d.',
                  max_steps,
                  max_steps / steps_per_epoch,
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
      steps=hparams['num_eval_images'] // eval_batch_size)
    tf.logging.info('Eval results at step %d: %s', next_checkpoint, eval_results)

  elapsed_time = int(time.time() - start_timestamp)
  tf.logging.info('Finished training up to step %d. Elapsed seconds %d.',
                  max_steps, elapsed_time)


  # export similar to Cloud ML Engine convention
  tf.logging.info('Starting to export model.')
  estimator.export_savedmodel(
    export_dir_base=os.path.join(output_dir, 'export/exporter'),
    serving_input_receiver_fn=serving_input_fn)
