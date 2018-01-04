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
from tensorflow.contrib.learn.python.learn import learn_runner

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--bucket',
      help='GCS path to data. We assume that data is in gs://BUCKET/txtcls1',
      required=True
  )
  parser.add_argument(
      '--output_dir',
      help='GCS location to write checkpoints and export models',
      required=True
  )
  parser.add_argument(
      '--train_steps',
      help='How many batches to run training job for',
      type=int,
      default=1000
  )
  parser.add_argument(
      '--glove_embedding',
      help='Pretrained embedding file. If omitted, will learn from training dataset',
      default=''
  )
  parser.add_argument(
      '--job-dir',
      help='this model ignores this field, but it is required by gcloud',
      default='junk'
  )

  args = parser.parse_args()
  arguments = args.__dict__
  
  # unused args provided by service
  arguments.pop('job_dir', None)
  arguments.pop('job-dir', None)

  output_dir = arguments.pop('output_dir')
  model.init(arguments)

  # Append trial_id to path if we are doing hptuning
  # This code can be removed if you are not using hyperparameter tuning
  output_dir = os.path.join(
      output_dir,
      json.loads(
          os.environ.get('TF_CONFIG', '{}')
      ).get('task', {}).get('trail', '')
  )

  # Run the training job
  learn_runner.run(model.make_experiment_fn(output_dir, arguments), output_dir)

