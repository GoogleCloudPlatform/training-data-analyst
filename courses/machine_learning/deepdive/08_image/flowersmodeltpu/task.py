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

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # Input Arguments
  parser.add_argument(
    '--train_batch_size',
    help='Batch size for training steps',
    type=int,
    default=256
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
    default=100
  )
  parser.add_argument(
    '--num_train_images',
    help='Number of training images',
    type=int,
    required=True
  )
  parser.add_argument(
    '--num_eval_images',
    help='Number of validation images',
    type=int,
    required=True
  )
  parser.add_argument(
    '--output_dir',
    help='GCS location to write checkpoints and export models',
    required=True
  )
  parser.add_argument(
    '--train_data_path',
    help='location of train file containing training tfrecords',
    required=True
  )
  parser.add_argument(
    '--eval_data_path',
    help='location of eval file containing evaluation tfrecords',
    required=True
  )
  parser.add_argument(
    '--job-dir',
    help='this model ignores this field, but it is required by gcloud',
    default='junk'
  )

  # for Cloud TPU
  parser.add_argument(
    '--use_tpu',
    help=('If specified, use TPU to execute the model for training and evaluation.'
          ' Else use whatever devices are available to'
          ' TensorFlow by default (e.g. CPU and GPU)'),
    dest='use_tpu',
    action='store_true')

  parser.add_argument(
    '--tpu', default=None,
    help='The Cloud TPU to use for training. This should be either the name '
         'used when creating the Cloud TPU, or a grpc://ip.address.of.tpu:8470 url.')

  parser.add_argument(
    '--project', default=None,
    help='Project name for the Cloud TPU-enabled project. If not specified, we '
         'will attempt to automatically detect the GCE project from metadata.')

  parser.add_argument(
    '--tpu_zone', default=None,
    help='GCE zone where the Cloud TPU is located in. If not specified, we '
         'will attempt to automatically detect the GCE project from metadata.')

  # optional hyperparameters used by cnn
  parser.add_argument(
    '--ksize1',
    help='kernel size of first layer for CNN',
    type=int,
    default=5)
  parser.add_argument(
    '--ksize2',
    help='kernel size of second layer for CNN',
    type=int,
    default=5)
  parser.add_argument(
    '--nfil1',
    help='number of filters in first layer for CNN',
    type=int,
    default=10)
  parser.add_argument(
    '--nfil2',
    help='number of filters in second layer for CNN',
    type=int,
    default=20)
  parser.add_argument(
    '--dprob',
    help='dropout probability for CNN',
    type=float,
    default=0.25)
  parser.add_argument(
    '--batch_norm',
    help='if specified, do batch_norm for CNN',
    dest='batch_norm',
    action='store_true')

  # boolean flags
  parser.set_defaults(use_tpu=False, batch_norm=False)

  args = parser.parse_args()
  hparams = args.__dict__
  print(hparams)

  output_dir = hparams.pop('output_dir')
  # Append trial_id to path for hptuning
  output_dir = os.path.join(
    output_dir,
    json.loads(
      os.environ.get('TF_CONFIG', '{}')
    ).get('task', {}).get('trial', '')
  )

  # Run the training job
  model.train_and_evaluate(output_dir, hparams)
