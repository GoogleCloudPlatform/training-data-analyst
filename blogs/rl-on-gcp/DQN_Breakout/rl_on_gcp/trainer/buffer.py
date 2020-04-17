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


"""Experience buffer for storing the Agent epsiodes  .

Each element in the buffer is in the form of
(state, action, next_state, reward, done)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from absl import flags
from collections import deque
from .utils import *
import numpy as np
import random

FLAGS = flags.FLAGS


class ExpBuffer():
  """Experience Buffer where the episode information is stored
  """

  def __init__(self, max_size=10000, min_size=5000):
    """ Initializes the maximum size of the buffer.
        Args:
          max_size: Height of the imag
    """
    self.buffer = deque()
    self.max_size = max_size
    self.min_size = min_size

  def add_exp(self, exp):
    """ Adds an experience to the buffer.

    """
    if len(self.buffer) > self.max_size:
      self.buffer.popleft()
    self.buffer.append(exp)

  def sample_experiences(self, batch_size=128):
    """ Samples experiences from the buffer.

        Returns: Sampled array from the experience buffer
    """

    sampled_buffer = random.sample(self.buffer, batch_size)
    state, next_state, reward, action, done = zip(*sampled_buffer)
    state, next_state = np.array(state), np.array(next_state)
    done, action = np.array(done), np.array(action)

    return (state, next_state, reward, action, done)
