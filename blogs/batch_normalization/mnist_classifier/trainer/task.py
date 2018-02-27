#!/usr/bin/env python

# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MNIST classifier.

Usage:
  trainer.task --outdir <outdir> [--batch_size <batch_size>] 
               [--num_steps <num_steps>] [--hidden_units <hidden_units>]
               [--use_batch_normalization] [--job-dir <job-dir>]

Options:
  -h --help     Show this screen.
  --batch_size <batch_size>  Batch size [default: 550]
  --num_steps <num_steps>  # training iterations [default: 100]
  --hidden_units <hidden_units>  Hidden units [default: 100]
  --use_batch_normalization  Use batch normalization
  --job-dir <job-dir>  This model ignores this field, but it's required for gcloud [default: blank]
"""
from docopt import docopt

from . import model


if __name__ == '__main__':
    arguments = docopt(__doc__)
    outdir = arguments['<outdir>']
    model.NUM_STEPS = int(arguments['--num_steps'])
    model.BATCH_SIZE = int(arguments['--batch_size'])
    model.HIDDEN_UNITS = [int(h) for h in arguments['--hidden_units'].split(',')]
    model.USE_BATCH_NORMALIZATION = arguments['--use_batch_normalization']
    model.train_and_evaluate(outdir)

