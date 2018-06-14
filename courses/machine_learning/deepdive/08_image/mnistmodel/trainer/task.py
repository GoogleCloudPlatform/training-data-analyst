# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Example implementation of image model in TensorFlow 
that can be trained and deployed on Cloud ML Engine
"""

import argparse
import json
import os

import model

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

def image_classifier(features, labels, mode, params):
  model_func = getattr(model, '{}_model'.format(params['model']))  # linear, dnn, cnn1, cnn2, etc.
  ylogits, nclasses = model_func(features['image'], mode, params)

  probabilities = tf.nn.softmax(ylogits)
  classes = tf.cast(tf.argmax(probabilities, 1), tf.uint8)
  if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=ylogits, labels=labels))
    evalmetrics =  {'accuracy': tf.metrics.accuracy(classes, tf.argmax(labels, 1))}
    if mode == tf.estimator.ModeKeys.TRAIN:
      # this is needed for batch normalization, but has no effect otherwise
      update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
      with tf.control_dependencies(update_ops):
         train_op = tf.contrib.layers.optimize_loss(loss, tf.train.get_global_step(),
                                                 learning_rate=params['learning_rate'], optimizer="Adam")
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
        export_outputs={'classes': tf.estimator.export.PredictOutput({"probabilities": probabilities, "classes": classes})}
    )

def train_and_evaluate(output_dir, hparams):
  EVAL_INTERVAL = 60
  estimator = tf.estimator.Estimator(model_fn = image_classifier,
                                     params = hparams,
                                     config= tf.estimator.RunConfig(save_checkpoints_secs = EVAL_INTERVAL),
                                     model_dir = output_dir)
  train_spec = tf.estimator.TrainSpec(input_fn = train_input_fn,
                                    max_steps = hparams['train_steps'])
  exporter = tf.estimator.LatestExporter('Servo', model.serving_input_fn)
  eval_spec = tf.estimator.EvalSpec(input_fn = eval_input_fn,
                                  steps = None,
                                  exporters = exporter,
                                  throttle_secs = EVAL_INTERVAL)
  tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # Input Arguments
  parser.add_argument(
      '--train_batch_size',
      help='Batch size for training steps',
      type=int,
      default=100
  )
  parser.add_argument(
      '--learning_rate',
      help='Initial learning rate for training',
      type=float,
      default=0.01
  )
  parser.add_argument(
      '--train_steps',
      help="""\
      Steps to run the training job for. A step is one batch-size,\
      """,
      type=int,
      default=0
  )
  parser.add_argument(
      '--output_dir',
      help='GCS location to write checkpoints and export models',
      required=True
  )
  model_names = [name.replace('_model','') \
                   for name in dir(model) \
                     if name.endswith('_model')]
  parser.add_argument(
      '--model',
      help='Type of model. Supported types are {}'.format(model_names),
      default='linear'
  )
  parser.add_argument(
      '--job-dir',
      help='this model ignores this field, but it is required by gcloud',
      default='junk'
  )

  # optional hyperparameters used by cnn
  parser.add_argument('--ksize1', help='kernel size of first layer for CNN', type=int, default=5)
  parser.add_argument('--ksize2', help='kernel size of second layer for CNN', type=int, default=5)
  parser.add_argument('--nfil1', help='number of filters in first layer for CNN', type=int, default=10)
  parser.add_argument('--nfil2', help='number of filters in second layer for CNN', type=int, default=20)
  parser.add_argument('--dprob', help='dropout probability for CNN', type=float, default=0.25)
  parser.add_argument('--batch_norm', help='if specified, do batch_norm for CNN', dest='batch_norm', action='store_true'); parser.set_defaults(batch_norm=False)

  args = parser.parse_args()
  hparams = args.__dict__
  
  # unused args provided by service
  hparams.pop('job_dir', None)
  hparams.pop('job-dir', None)

  output_dir = hparams.pop('output_dir')
  # Append trial_id to path for hptuning
  output_dir = os.path.join(
      output_dir,
      json.loads(
          os.environ.get('TF_CONFIG', '{}')
      ).get('task', {}).get('trial', '')
  )

  # calculate train_steps if not provided
  if hparams['train_steps'] < 1:
     # 10,000 steps at batch_size of 512
     hparams['train_steps'] = (10000 * 512) // hparams['train_batch_size']
     print "Training for {} steps".format(hparams['train_steps'])
  
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
  # Run the training job
  train_and_evaluate(output_dir, hparams)

