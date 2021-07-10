# Copyright 2019 Google Inc. All Rights Reserved.
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

"""An Actor-Critic model to show reinforcement learning on the cloud."""

from collections import deque
import random

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import tensorflow.keras.backend as K
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import Model

CLIP_EDGE = 1e-8


# Create agent components
def build_networks(
        state_shape, action_size, learning_rate,
        critic_weight, hidden_neurons, entropy):
    """Creates Actor Critic Neural Networks.

    Creates a two hidden-layer Policy Gradient Neural Network. The loss
    function is altered to be a log-likelihood function weighted
    by an action's advantage.

    Args:
        space_shape: a tuple of ints representing the observation space.
        action_size (int): the number of possible actions.
        learning_rate (float): the nueral network's learning rate.
        critic_weight (float): how much to weigh the critic's training loss.
        hidden_neurons (int): the number of neurons to use per hidden layer.
        entropy (float): how much to enourage exploration versus exploitation.
    """
    state_input = layers.Input(state_shape, name='frames')
    advantages = layers.Input((1,), name='advantages')

    actor_1 = layers.Dense(hidden_neurons, activation='relu')(state_input)
    actor_2 = layers.Dense(hidden_neurons, activation='relu')(actor_1)
    probabilities = layers.Dense(action_size, activation='softmax')(actor_2)

    critic_1 = layers.Dense(hidden_neurons, activation='relu')(state_input)
    critic_2 = layers.Dense(hidden_neurons, activation='relu')(critic_1)
    values = layers.Dense(1, activation='linear')(critic_2)

    def actor_loss(y_true, y_pred):
        y_pred_clipped = K.clip(y_pred, CLIP_EDGE, 1-CLIP_EDGE)
        log_lik = y_true*K.log(y_pred_clipped)
        entropy_loss = y_pred * K.log(K.clip(y_pred, CLIP_EDGE, 1-CLIP_EDGE))
        return K.sum(-log_lik * advantages) - (entropy * K.sum(entropy_loss))

    # Train both actor and critic at the same time.
    actor = Model(
        inputs=[state_input, advantages], outputs=[probabilities, values])
    actor.compile(
        loss=[actor_loss, 'mean_squared_error'],
        loss_weights=[1, critic_weight],
        optimizer=tf.keras.optimizers.Adam(lr=learning_rate))

    critic = Model(inputs=[state_input], outputs=[values])
    policy = Model(inputs=[state_input], outputs=[probabilities])
    return actor, critic, policy


class Memory():
    """Sets up a memory replay for actor-critic training.

    Args:
        gamma (float): The "discount rate" used to assess state values.
        batch_size (int): The number of elements to include in the buffer.
    """
    def __init__(self, gamma, batch_size):
        self.buffer = []
        self.gamma = gamma
        self.batch_size = batch_size

    def add(self, experience):
        """Adds an experience into the memory buffer.

        Args:
            experience: (state, action, reward, state_prime_value, done) tuple.
        """
        self.buffer.append(experience)

    def check_full(self):
        return len(self.buffer) >= self.batch_size

    def sample(self):
        """Returns formated experiences and clears the buffer.

        Returns:
            (list): A tuple of lists with structure [
                [states], [actions], [rewards], [state_prime_values], [dones]
            ]
        """
        # Columns have different data types, so numpy array would be awkward.
        batch = np.array(self.buffer).T.tolist()
        states_mb = np.array(batch[0], dtype=np.float32)
        actions_mb = np.array(batch[1], dtype=np.int8)
        rewards_mb = np.array(batch[2], dtype=np.float32)
        dones_mb = np.array(batch[3], dtype=np.int8)
        value_mb = np.squeeze(np.array(batch[4], dtype=np.float32))
        self.buffer = []
        return states_mb, actions_mb, rewards_mb, dones_mb, value_mb


class Agent():
    """Sets up a reinforcement learning agent to play in a game environment."""
    def __init__(self, actor, critic, policy, memory, action_size):
        """Initializes the agent with DQN and memory sub-classes.

        Args:
            network: A neural network created from deep_q_network().
            memory: A Memory class object.
            epsilon_decay (float): The rate at which to decay random actions.
            action_size (int): The number of possible actions to take.
        """
        self.actor = actor
        self.critic = critic
        self.policy = policy
        self.action_size = action_size
        self.memory = memory

    def act(self, state):
        """Selects an action for the agent to take given a game state.

        Args:
            state (list of numbers): The state of the environment to act on.
            traning (bool): True if the agent is training.

        Returns:
            (int) The index of the action to take.
        """
        # If not acting randomly, take action with highest predicted value.
        state_batch = np.expand_dims(state, axis=0)
        probabilities = self.policy.predict(state_batch)[0]
        action = np.random.choice(self.action_size, p=probabilities)
        return action

    def learn(self):
        """Trains the Deep Q Network based on stored experiences."""
        gamma = self.memory.gamma
        experiences = self.memory.sample()
        state_mb, action_mb, reward_mb, dones_mb, next_value = experiences

        # One hot enocde actions
        actions = np.zeros([len(action_mb), self.action_size])
        actions[np.arange(len(action_mb)), action_mb] = 1

        # Apply TD(0)
        discount_mb = reward_mb + next_value * gamma * (1 - dones_mb)
        state_values = self.critic.predict([state_mb])
        advantages = discount_mb - np.squeeze(state_values)
        self.actor.train_on_batch(
            [state_mb, advantages], [actions, discount_mb])
