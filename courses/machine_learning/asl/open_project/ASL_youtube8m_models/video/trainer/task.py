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

import shutil
import tensorflow as tf

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Input Arguments
    parser.add_argument(
        '--train_file_pattern',
        help = 'GCS or local path and pattern to training data',
        required = True
    )
    parser.add_argument(
        '--eval_file_pattern',
        help = 'GCS or local path to evaluation data',
        required = True
    )
    parser.add_argument(
        '--output_dir',
        help = 'GCS location to write checkpoints and export models',
        required = True
    )
    parser.add_argument(
        '--job-dir',
        help = 'this model ignores this field, but it is required by gcloud',
        default = 'junk'
    )
    parser.add_argument(
        '--batch_size',
        help = 'Specify number of batch size',
        default = 10,
        type = int
    )
    parser.add_argument(
        '--train_steps',
        help = 'Specify number of steps(batches) to train for',
        default = 1000,
        type = int
    )
    parser.add_argument(
        '--hidden_units',
        help = 'The number of hidden units per hidden layer',
        default = "1024 256 64",
        type = str
    )
    parser.add_argument(
        '--top_k',
        help = 'The top k highest probable classes to be returned',
        default = 5,
        type = int
    )
    # Eval arguments
    parser.add_argument(
        '--start_delay_secs',
        help = 'Start evaluating after waiting for this many seconds',
        default = 60,
        type = int
    )
    parser.add_argument(
        '--throttle_secs',
        help = 'Do not re-evaluate unless the last evaluation was started at least this many seconds ago. Of course, evaluation does not occur if no new checkpoints are available, hence, this is the minimum',
        default = 30,
        type = int
    )

    args = parser.parse_args()
    arguments = args.__dict__
    
    # Unused args provided by service
    arguments.pop('job_dir', None)
    arguments.pop('job-dir', None)

    # Append trial_id to path if we are doing hptuning
    # This code can be removed if you are not using hyperparameter tuning
    arguments['output_dir'] = os.path.join(
        arguments['output_dir'],
        json.loads(
            os.environ.get('TF_CONFIG', '{}')
        ).get('task', {}).get('trial', '')
    )
    
    arguments['hidden_units'] = [int(x) for x in arguments['hidden_units'].split(' ')]

    # Run the training job
    try:
        shutil.rmtree(arguments['output_dir'], ignore_errors = True) # start fresh each time
        model.train_and_evaluate(arguments)
    except:
        traceback.print_exc()