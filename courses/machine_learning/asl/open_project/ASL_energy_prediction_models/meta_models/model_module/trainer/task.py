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

import shutil

import model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output_dir',
        help = 'GCS location to write checkpoints and export models',
        required = True
    )
    parser.add_argument(
        '--train_file_pattern',
        help = 'GCS location to read training data from',
        required = True
    )
    parser.add_argument(
        '--eval_file_pattern',
        help = 'GCS location to read validation data from',
        required = True
    )
    parser.add_argument(
        '--model_fn_name',
        help = 'The name of the model function to use',
        type = str,
        required = True
    )
    parser.add_argument(
        '--train_steps',
        help = 'Number of steps(batches) to train for',
        type = int,
        default = 1000
    )
    parser.add_argument(
        '--batch_size',
        help = 'Number of examples to compute gradient over',
        type = int,
        default = 512
    )
    parser.add_argument(
        '--input_sequence_length',
        help = 'Number of examples to use as the features',
        type = int,
        default = 1
    )
    parser.add_argument(
        '--horizon',
        help = 'Number of examples to skip between the input and output sequences',
        type = int,
        default = 0
    )
    parser.add_argument(
        '--output_sequence_length',
        help = 'Number of examples to use as the labels',
        type = int,
        default = 1
    )
    parser.add_argument(
        '--reverse_sequence',
        help = 'If True, we reverse sequence',
        type = bool,
        default = False
    )
    parser.add_argument(
        '--lstm_hidden_units',
        help = 'Hidden layer sizes to use for LSTMs -- provide space-separated layers',
        type = str,
        default = "128 32 4"
    )
    parser.add_argument(
        '--lstm_dropout_output_keep_probs',
        help = 'Dropout output keep probabilities to use for LSTMs -- provide space-separated layers',
        type = str,
        default = "0.95 1.0 1.0"
    )
    parser.add_argument(
        '--dnn_hidden_units',
        help = 'Hidden layer sizes to use for DNN -- provide space-separated layers',
        type = str,
        default = "128 32 4"
    )
    parser.add_argument(
        '--learning_rate',
        help = 'This multiplied by the gradient determines weight stepsize',
        type = float,
        default = 0.01
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
    parser.add_argument(
        '--job-dir',
        help = 'this model ignores this field, but it is required by gcloud',
        default = 'junk'
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

    arguments['train_steps'] = max(1, arguments['train_steps'])
    arguments['batch_size'] = max(1, arguments['batch_size'])
    arguments['input_sequence_length'] = max(1, arguments['input_sequence_length'])
    arguments['horizon'] = max(0, arguments['horizon'])
    arguments['output_sequence_length'] = max(1, arguments['output_sequence_length'])
    
    arguments['lstm_hidden_units'] = [int(x) for x in arguments['lstm_hidden_units'].split(' ')]
    print ("Will use LSTM size of {}".format(arguments['lstm_hidden_units']))
    
    arguments['lstm_dropout_output_keep_probs'] = [float(x) for x in arguments['lstm_dropout_output_keep_probs'].split(' ')]
    print ("Will use LSTM output keep probabilities of {}".format(arguments['lstm_dropout_output_keep_probs']))
    
    arguments['dnn_hidden_units'] = [int(x) for x in arguments['dnn_hidden_units'].split(' ')]
    print ("Will use DNN size of {}".format(arguments['dnn_hidden_units']))

    # Run the training job
    try:
        shutil.rmtree(arguments['output_dir'], ignore_errors = True) # start fresh each time
        model.train_and_evaluate(args = arguments)
    except:
        traceback.print_exc()
