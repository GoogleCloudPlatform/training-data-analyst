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

"""Example implementation of code to run on the Cloud ML service.
"""

import traceback
import argparse
import json
import os

import model

import tensorflow as tf
from tensorflow.contrib.learn.python.learn import learn_runner
from tensorflow.contrib.learn.python.learn.utils import (
    saved_model_export_utils)

def compute_errors(features, labels, predictions):
   if predictions.shape[1] == 1:
      loss = tf.losses.mean_squared_error(labels, predictions)
      rmse = tf.metrics.root_mean_squared_error(labels, predictions)
      return loss, rmse
   else:
      # one prediction for every input in sequence
      # get 1-N of (x + label)
      labelsN = tf.concat([features[model.TIMESERIES_COL], labels], axis=1)
      labelsN = labelsN[:, 1:]
      # loss is computed from the last 1/3 of the series
      N = (2 * model.N_INPUTS) // 3
      loss = tf.losses.mean_squared_error(labelsN[:, N:], predictions[:, N:])
      # rmse is computed from last prediction and last label
      lastPred = predictions[:, -1]
      rmse = tf.metrics.root_mean_squared_error(labels, lastPred)
      return loss, rmse

# create the inference model
def sequence_regressor(features, labels, mode, params):

  # 1. run the appropriate model
  model_func = getattr(model, '{}_model'.format(params['model']))  # models available
  predictions = model_func(features, mode, params)

  # 2. loss function, training/eval ops
  loss = None
  train_op = None
  eval_metric_ops = None
  if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
     loss, rmse = compute_errors(features, labels, predictions)

     if mode == tf.estimator.ModeKeys.TRAIN:
        # this is needed for batch normalization, but has no effect otherwise
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
           # 2b. set up training operation
           train_op = tf.contrib.layers.optimize_loss(
              loss,
              tf.train.get_global_step(),
              learning_rate=params['learning_rate'],
              optimizer="Adam")
 
     # 2c. eval metric
     eval_metric_ops = {
      "rmse": rmse
     }

  # 3. Create predictions
  if predictions.shape[1] != 1:
     predictions = predictions[:, -1] # last predicted value
  predictions_dict = {"predicted": predictions}

  # 4. return EstimatorSpec
  return tf.estimator.EstimatorSpec(
      mode=mode,
      predictions=predictions_dict,
      loss=loss,
      train_op=train_op,
      eval_metric_ops=eval_metric_ops,
      export_outputs={'predictions': tf.estimator.export.PredictOutput(predictions_dict)}
  )



def create_custom_estimator(output_dir, hparams):
  save_freq = max(1, min(100, hparams['train_steps']/100))
  training_config = tf.contrib.learn.RunConfig(save_checkpoints_secs=None,
                                               save_checkpoints_steps=save_freq)
  return tf.estimator.Estimator(model_fn=sequence_regressor, model_dir=output_dir,
                                config=training_config, params=hparams)


def generate_experiment_fn(output_dir, hparams):
 def experiment_fn(output_dir):
    get_train = model.read_dataset(hparams['train_data_paths'],
                                   tf.estimator.ModeKeys.TRAIN,
                                   hparams['train_batch_size'])
    get_valid = model.read_dataset(hparams['eval_data_paths'],
                                   tf.estimator.ModeKeys.EVAL,
                                   1000)
    eval_freq = max(1, min(2000, hparams['train_steps']/5))

    return tf.contrib.learn.Experiment(
        estimator=create_custom_estimator(output_dir, hparams),
        train_input_fn=get_train,
        eval_input_fn=get_valid,
        train_steps=hparams['train_steps'],
        eval_steps=1,
        min_eval_frequency=eval_freq,
        export_strategies=[saved_model_export_utils.make_export_strategy(
            model.serving_input_fn,
            default_output_alternative_key=None,
            exports_to_keep=1
        )]
    )
 return experiment_fn

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # Input Arguments
  parser.add_argument(
      '--train_data_paths',
      help='GCS or local path to training data',
      required=True
  )
  parser.add_argument(
      '--eval_data_paths',
      help='GCS or local path to evaluation data',
      required=True
  )
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
      '--sequence_length',
      help="""\
      This model works with fixed length sequences. 1-(N-1) are inputs, last is output
      """,
      type=int,
      default=10
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
      required=True
  )
  parser.add_argument(
      '--job-dir',
      help='this model ignores this field, but it is required by gcloud',
      default='junk'
  )

  # Experiment hparams
  parser.add_argument(
      '--eval_delay_secs',
      help='How long to wait before running first evaluation',
      default=10,
      type=int
  )
  parser.add_argument(
      '--min_eval_frequency',
      help='Minimum number of training steps between evaluations',
      default=1,
      type=int
  )

  args = parser.parse_args()
  hparams = args.__dict__
  
  # unused args provided by service
  hparams.pop('job_dir', None)
  hparams.pop('job-dir', None)

  output_dir = hparams.pop('output_dir')

  # Append trial_id to path if we are doing hptuning
  # This code can be removed if you are not using hyperparameter tuning
  output_dir = os.path.join(
      output_dir,
      json.loads(
          os.environ.get('TF_CONFIG', '{}')
      ).get('task', {}).get('trial', '')
  )

  # calculate train_steps if not provided
  if hparams['train_steps'] < 1:
     # 1,000 steps at batch_size of 100
     hparams['train_steps'] = (1000 * 100) // hparams['train_batch_size']
     print ("Training for {} steps".format(hparams['train_steps']))

  model.init(hparams)

  # Run the training job
  try:
     learn_runner.run(generate_experiment_fn(output_dir, hparams), output_dir)
  except:
     traceback.print_exc()

