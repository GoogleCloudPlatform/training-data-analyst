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
import shutil

from . import model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Input and output paths
    parser.add_argument(
        '--bucket',
        help = 'GCS path to training data',
        required = True
    )
    parser.add_argument(
        '--train_data_paths',
        help = 'GCS path to training data',
        required = True
    )
    parser.add_argument(
        '--eval_data_paths',
        help = 'GCS path to validation data',
        required = True
    )
    parser.add_argument(
        '--output_dir',
        help = 'GCS pat to write checkpoints and export models',
        required = True
    )
    # Tunable hyperparameters
    parser.add_argument(
        '--batch_size',
        help = 'The number of examples in each mini-batch',
        type = int,
        default = 512
    )
    parser.add_argument(
        '--learning_rate',
        help = 'The learning rate for gradient descent',
        type = float,
        default = 0.1
    )
    parser.add_argument(
        '--hidden_units',
        help = 'Hidden layer sizes to use for DNN feature columns -- provide space-separated layers',
        type = str,
        default = "128 32 4"
    )
    parser.add_argument(
        '--content_id_embedding_dimensions',
        help = 'The number of dimensions to embed content id feature into',
        type = int,
        default = 20
    )
    parser.add_argument(
        '--author_embedding_dimensions',
        help = 'The number of dimensions to embed author feature into',
        type = int,
        default = 10
    )
    # Training/evaluation loop parameters
    parser.add_argument(
        '--top_k',
        help = 'The top k classes to calculate the accuracy on',
        type = int,
        default = 10
    )
    parser.add_argument(
        '--train_steps',
        help = 'The number of steps/batches to train on',
        type = int,
        default = 100
    )
    parser.add_argument(
        '--start_delay_secs',
        help = 'The number of seconds to delay before starting evaluation',
        type = int,
        default = 30
    )
    parser.add_argument(
        '--throttle_secs',
        help = 'The number of seconds between each evaluation',
        type = int,
        default = 60
    )
    parser.add_argument(
        '--job-dir',
        help = 'this model ignores this field, but it is required by gcloud',
        default = 'junk'
    )

    args = parser.parse_args()
    arguments = args.__dict__

    # unused args provided by service
    arguments.pop('job_dir', None)
    arguments.pop('job-dir', None)
    
    # Create hidden_units list
    arguments['hidden_units'] = [int(x) for x in arguments['hidden_units'].split(" ")]

    # Append trial_id to path if we are doing hptuning
    # This code can be removed if you are not using hyperparameter tuning
    arguments['output_dir'] = os.path.join(
        arguments['output_dir'],
        json.loads(
            os.environ.get('TF_CONFIG', '{}')
        ).get('task', {}).get('trial', '')
    )

    # Run the training job
    shutil.rmtree(arguments['output_dir'], ignore_errors = True) # start fresh each time
    model.build_model(arguments)
