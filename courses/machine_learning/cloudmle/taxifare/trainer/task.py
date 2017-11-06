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

import argparse
import json
import os

import model

import tensorflow as tf
from tensorflow.contrib.learn import Experiment
from tensorflow.contrib.learn.python.learn import learn_runner
from tensorflow.contrib.learn.python.learn.utils import (
    saved_model_export_utils)


def generate_experiment_fn(train_data_paths,
                           eval_data_paths,
                           format,
                           num_epochs=None,
                           train_batch_size=512,
                           eval_batch_size=512,
                           hidden_units=None,
                           **experiment_args):

  def _experiment_fn(output_dir):
    input_fn = model.generate_csv_input_fn
    train_input = input_fn(
        train_data_paths, num_epochs=num_epochs, batch_size=train_batch_size)
    eval_input = input_fn(
        eval_data_paths, batch_size=eval_batch_size, mode=tf.contrib.learn.ModeKeys.EVAL)
    return Experiment(
        model.build_estimator(
            output_dir,
            hidden_units=hidden_units
        ),
        train_input_fn=train_input,
        eval_input_fn=eval_input,
        export_strategies=[saved_model_export_utils.make_export_strategy(
            model.serving_input_fn,
            default_output_alternative_key=None,
            exports_to_keep=1
        )],
        eval_metrics=model.get_eval_metrics(),
        #min_eval_frequency = 1000,  # change this to speed up training on large datasets
        **experiment_args
    )
  return _experiment_fn


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # Input Arguments
  parser.add_argument(
      '--train_data_paths',
      help='GCS or local path to training data',
      required=True
  )
  parser.add_argument(
      '--num_epochs',
      help="""\
      Maximum number of training data epochs on which to train.
      If both --max-steps and --num-epochs are specified,
      the training job will run for --max-steps or --num-epochs,
      whichever occurs first. If unspecified will run for --max-steps.\
      """,
      type=int,
  )
  parser.add_argument(
      '--train_batch_size',
      help='Batch size for training steps',
      type=int,
      default=512
  )
  parser.add_argument(
      '--eval_batch_size',
      help='Batch size for evaluation steps',
      type=int,
      default=512
  )
  parser.add_argument(
      '--train_steps',
      help="""\
      Steps to run the training job for. If --num-epochs is not specified,
      this must be. Otherwise the training job will run indefinitely.\
      """,
      type=int
  )
  parser.add_argument(
      '--eval_steps',
      help='Number of steps to run evalution for at each checkpoint',
      default=10,
      type=int
  )
  parser.add_argument(
      '--eval_data_paths',
      help='GCS or local path to evaluation data',
      required=True
  )
  # Training arguments
  parser.add_argument(
      '--hidden_units',
      help='List of hidden layer sizes to use for DNN feature columns',
      nargs='+',
      type=int,
      default=[128, 32, 4]
  )
  parser.add_argument(
      '--output_dir',
      help='GCS location to write checkpoints and export models',
      required=True
  )
  parser.add_argument(
      '--job-dir',
      help='this model ignores this field, but it is required by gcloud',
      default='junk'
  )

  # Experiment arguments
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
  parser.add_argument(
      '--format',
      help='Is the input data format csv or tfrecord?',
      default='csv',
  )

  args = parser.parse_args()
  arguments = args.__dict__
  
  # unused args provided by service
  arguments.pop('job_dir', None)
  arguments.pop('job-dir', None)

  output_dir = arguments.pop('output_dir')
  # Append trial_id to path if we are doing hptuning
  # This code can be removed if you are not using hyperparameter tuning
  output_dir = os.path.join(
      output_dir,
      json.loads(
          os.environ.get('TF_CONFIG', '{}')
      ).get('task', {}).get('trial', '')
  )

  # Run the training job
  learn_runner.run(generate_experiment_fn(**arguments), output_dir)

