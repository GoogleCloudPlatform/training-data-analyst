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


"""Commmon helper functions

This module imports all the pre-processing functions for the state space..
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import os

import numpy as np
import tensorflow as tf
from absl import app
from absl import flags

FLAGS = flags.FLAGS
GREY_FILTER= [0.299, 0.587, 0.114]

def downsample_state(observation, image_height=84, image_width=84, image_channels=1):
  """Downsamples the Observations to a lower resolution.
  Args:
    observation(array):
    downscale_height(int):
    downscale_width(int):

  Returns:
     Downsampled image
  """
  return np.resize(observation, (image_height, image_width, image_channels))


def convert_greyscale(observation):
  """Converts the RGB Image to greyscale.
  Args:
    observation(array):
  Returns:
    Greyscale observation(array):
  """
  greyscale_image = np.dot(observation[..., :3], GREY_FILTER)
  greyscale_image = np.expand_dims(greyscale_image, axis=-1)
  return greyscale_image


def anneal_exploration(eta,
                       curr_step,
                       max_step,
                       train_step,
                       init_val=0.99,
                       min_eta=0.1,
                       type="linear"):
  """ Anneals the probability of the agent to take random actions.

  Args:
    eta(float): current random value betwee 0 and 1
    current_steps(int): Current number of steps taken by the agent
    total_steps(int): Total number of steps for the simulation

  Returns:

  """
  if type == "linear" and curr_step > train_step:
    decay_value = ((curr_step - train_step) / float(max_step)) * (
        init_val - min_eta)
    eta = init_val - decay_value
    eta = max(eta, min_eta)
  #TODO:(praneetdutta): Add exponential decay function
  return eta

def huber_loss(Q_true, Q_estimate):
  """ Huber loss implemented  as per the original DQN paper.

    Args:
      Q_true: Ground truth Q-Value for future states
      Q_estimate: Predicted Q-Value

    Returns:
      tf.losses.huber_loss: Tensorflow Loss function
    """
  return tf.losses.huber_loss(Q_true, Q_estimate)


def hp_directory(model_dir):
  """If running a hyperparam job, create subfolder name with trial ID.

  If not running a hyperparam job, just keep original model_dir."""
  trial_id = json.loads(
            os.environ.get('TF_CONFIG', '{}')
        ).get('task', {}).get('trial', '')
  return os.path.join(model_dir, trial_id)
