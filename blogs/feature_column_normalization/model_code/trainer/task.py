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

"""task.py. Call the housing dataset model using feature_column normalization.

Usage:
  task.py [--outdir=location] [--normalize_inputs=normalize]

Options:
  -h --help     Show this screen.
  --outdir=<location>  Location to save model checkpoints. [default: ...].
  --normalize_inputs=<normalize>  Normalize feature_columns. [default: 0].
"""

from docopt import docopt

from . import model

if __name__ == '__main__':
    arguments = docopt(__doc__)
    outdir = arguments['--outdir']
    use_normalization = int(arguments['--normalize_inputs'])
    model.train_and_evaluate(use_normalization, outdir)
