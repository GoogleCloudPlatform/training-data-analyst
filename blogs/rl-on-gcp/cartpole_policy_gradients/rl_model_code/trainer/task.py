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
"""Simple refinforcement on Google Cloud Platform example.
Usage:
    trainer.task --outdir=<name>
                 [--eval]
                 [--n_games_per_update=<N>]
                 [--n_hidden=<N>]
                 [--discount_rate=<rate>]
                 [--learning_rate=<rate>]

Options:
    -h, --help  Show this screen and exit.
    --eval  If in eval, make a gif.
    --outdir=<name> Location to save model (or of saved model if eval).
    --n_games_per_update=<N> Number of games to play.  [default: 10]
    --n_hidden=<N>  # of hidden units [default: 10]
    --discount_rate=<rate>  Reward discount rate. [default: 0.95]
    --learning_rate=<rate>  Learning rate. [default: 0.01]
"""
from docopt import docopt

from . import model

arguments = docopt(__doc__)

# Update hyperparameters in model.py.
model.DISCOUNT_RATE = float(arguments['--discount_rate'])
model.LEARNING_RATE = float(arguments['--learning_rate'])
model.N_HIDDEN = int(arguments['--n_hidden'])
model.N_GAMES_PER_UPDATE = int(arguments['--n_games_per_update'])
# Train.
in_train_mode =  not arguments['--eval']
print(arguments)
model.run(arguments['--outdir'], in_train_mode)
