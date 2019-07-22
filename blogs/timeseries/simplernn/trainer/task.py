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
import tensorflow.contrib.learn as tflearn
from tensorflow.contrib.learn.python.learn import learn_runner
from tensorflow.contrib.learn.python.learn.utils import (
    saved_model_export_utils)

def generate_experiment_fn(train_data_paths, eval_data_paths, **experiment_args):
 def experiment_fn(output_dir):
    get_train = model.read_dataset(train_data_paths, mode=tf.contrib.learn.ModeKeys.TRAIN)
    get_valid = model.read_dataset(eval_data_paths, mode=tf.contrib.learn.ModeKeys.EVAL)
    # run experiment
    return tflearn.Experiment(
        tflearn.Estimator(model_fn=model.simple_rnn, model_dir=output_dir),
        train_input_fn=get_train,
        eval_input_fn=get_valid,
        eval_metrics={
            'rmse': tflearn.MetricSpec(
                metric_fn=tf.contrib.metrics.streaming_root_mean_squared_error
            )
        },
        export_strategies=[saved_model_export_utils.make_export_strategy(
            model.serving_input_fn,
            default_output_alternative_key=None,
            exports_to_keep=1
        )],
        **experiment_args
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

  # Run the training job:w
  try:
     learn_runner.run(generate_experiment_fn(**arguments), output_dir)
  except:
     traceback.print_exc()

