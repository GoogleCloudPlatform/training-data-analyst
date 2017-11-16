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
      help='GCS path to data. We assume that data is in gs://BUCKET/babyweight/preproc/',
      required=True
  )
  parser.add_argument(
      '--output_dir',
      help='GCS location to write checkpoints and export models',
      required=True
  )
  parser.add_argument(
      '--train_examples',
      help='Number of examples (in thousands) to run the training job over. If this is more than actual # of examples available, it cycles through them. So specifying 1000 here when you have only 100k examples makes this 10 epochs.',
      type=int,
      default=5000
  )
  parser.add_argument(
      '--batch_size',
      help='Number of examples to compute gradient over.',
      type=int,
      default=512
  )
  parser.add_argument(
      '--nbuckets',
      help='Embedding size of a cross of 3 key real-valued parameters',
      type=int,
      default=10
  )
  parser.add_argument(
      '--nnsize',
      help='Hidden layer sizes to use for DNN feature columns -- provide space-separated layers',
      default='64 32'
  )
  parser.add_argument(
      '--pattern',
      help='Specify a pattern that has to be in input files. For example 00001-of will process only one shard',
      default='of'
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
  model.BUCKET     = arguments.pop('bucket')
  model.BATCH_SIZE = arguments.pop('batch_size')
  model.TRAIN_STEPS = (arguments.pop('train_examples') * 1000) / model.BATCH_SIZE
  print ("Will train for {} steps using batch_size={}".format(model.TRAIN_STEPS, model.BATCH_SIZE))
  model.PATTERN = arguments.pop('pattern')
  model.NBUCKETS= arguments.pop('nbuckets')
  model.NNSIZE = [ int(p) for p in arguments.pop('nnsize').split(' ')]

  # Append trial_id to path if we are doing hptuning
  # This code can be removed if you are not using hyperparameter tuning
  output_dir = os.path.join(
      output_dir,
      json.loads(
          os.environ.get('TF_CONFIG', '{}')
      ).get('task', {}).get('trial', '')
  )

  # Run the training job
  learn_runner.run(model.experiment_fn, output_dir)
