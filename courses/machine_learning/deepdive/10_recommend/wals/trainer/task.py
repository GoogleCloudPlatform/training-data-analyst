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
      '--input_path',
      help='Path to data, either local or on GCS. We will append /users_for_item or /items_for_user',
      required=True
  )
  parser.add_argument(
      '--output_dir',
      help='GCS location to write checkpoints and export models',
      required=True
  )
  parser.add_argument(
      '--num_epochs',
      help='Number of times to iterate over the training dataset. This can be fractional',
      type=float,
      default=5
  )
  parser.add_argument(
      '--batch_size',
      help='Matrix factorization happens in chunks. Specify chunk size here.',
      type=int,
      default=512
  )
  parser.add_argument(
      '--n_embeds',
      help='Number of dimensions to use for the embedding dimension',
      type=int,
      default=10
  )
  parser.add_argument(
      '--nusers',
      help='Total number of users. WALS expects userId to be indexed 0,1,2,... ',
      type=int,
      required=True
  )
  parser.add_argument(
      '--nitems',
      help='Total number of items. WALS expects itemId to be indexed 0,1,2,... ',
      type=int,
      required=True
  )
  parser.add_argument(
      '--topk',
      help='In batch prediction, how many top items should we emit for each user?',
      type=int,
      default=3
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

  # Append trial_id to path if we are doing hptuning
  # This code can be removed if you are not using hyperparameter tuning
  output_dir = arguments['output_dir']
  output_dir = os.path.join(
      output_dir,
      json.loads(
          os.environ.get('TF_CONFIG', '{}')
      ).get('task', {}).get('trial', '')
  )

  # Run the training job
  model.train_and_evaluate(arguments)
