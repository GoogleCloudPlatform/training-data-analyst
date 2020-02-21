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

"""A deep Q network to show reinforcement learning on the cloud."""

from collections import deque
import random

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models


# Create agent components
def deep_q_network(
        state_shape, action_size, learning_rate, hidden_neurons):
    """Creates a Deep Q Network to emulate Q-learning.

    Creates a two hidden-layer Deep Q Network. Similar to a typical nueral
    network, the loss function is altered to reduce the difference between
    predicted Q-values and Target Q-values.

    Args:
        space_shape: a tuple of ints representing the observation space.
        action_size (int): the number of possible actions.
        learning_rate (float): the nueral network's learning rate.
        hidden_neurons (int): the number of neurons to use per hidden
            layer.
    """
    state_input = layers.Input(state_shape, name='frames')
    actions_input = layers.Input((action_size,), name='mask')

    hidden_1 = layers.Dense(hidden_neurons, activation='relu')(state_input)
    hidden_2 = layers.Dense(hidden_neurons, activation='relu')(hidden_1)
    q_values = layers.Dense(action_size)(hidden_2)
    masked_q_values = layers.Multiply()([q_values, actions_input])

    model = models.Model(
        inputs=[state_input, actions_input], outputs=masked_q_values)
    optimizer = tf.keras.optimizers.RMSprop(lr=learning_rate)
    model.compile(loss='mse', optimizer=optimizer)
    return model


class Memory():
    """Sets up a memory replay buffer for a Deep Q Network.

    A simple memory buffer for a DQN. This one randomly selects state
    transitions with uniform probability, but research has gone into
    other methods. For instance, a weight could be given to each memory
    depending on how big of a difference there is between predicted Q values
    and target Q values.

    Args:
        memory_size (int): How many elements to hold in the memory buffer.
        batch_size (int): The number of elements to include in a replay batch.
        gamma (float): The "discount rate" used to assess Q values.
    """
    def __init__(self, memory_size, batch_size, gamma):
        self.buffer = deque(maxlen=memory_size)
        self.batch_size = batch_size
        self.gamma = gamma

    def add(self, experience):
        """Adds an experience into the memory buffer.

        Args:
            experience: a (state, action, reward, state_prime, done) tuple.
        """
        self.buffer.append(experience)

    def sample(self):
        """Uniformally selects from the replay memory buffer.

        Uniformally and randomly selects experiences to train the nueral
        network on. Transposes the experiences to allow batch math on
        the experience components.

        Returns:
            (list): A list of lists with structure [
                [states], [actions], [rewards], [state_primes], [dones]
            ]
        """
        buffer_size = len(self.buffer)
        index = np.random.choice(
            np.arange(buffer_size), size=self.batch_size, replace=False)

        # Columns have different data types, so numpy array would be awkward.
        batch = np.array([self.buffer[i] for i in index]).T.tolist()
        states_mb = tf.convert_to_tensor(np.array(batch[0], dtype=np.float32))
        actions_mb = np.array(batch[1], dtype=np.int8)
        rewards_mb = np.array(batch[2], dtype=np.float32)
        states_prime_mb = np.array(batch[3], dtype=np.float32)
        dones_mb = batch[4]
        return states_mb, actions_mb, rewards_mb, states_prime_mb, dones_mb


class Agent():
    """Sets up a reinforcement learning agent to play in a game environment."""
    def __init__(self, network, memory, epsilon_decay, action_size):
        """Initializes the agent with DQN and memory sub-classes.

        Args:
            network: A neural network created from deep_q_network().
            memory: A Memory class object.
            epsilon_decay (float): The rate at which to decay random actions.
            action_size (int): The number of possible actions to take.
        """
        self.network = network
        self.action_size = action_size
        self.memory = memory
        self.epsilon = 1  # The chance to take a random action.
        self.epsilon_decay = epsilon_decay

    def act(self, state, training=False):
        """Selects an action for the agent to take given a game state.

        Args:
            state (list of numbers): The state of the environment to act on.
            traning (bool): True if the agent is training.

        Returns:
            (int) The index of the action to take.
        """
        if training:
            # Random actions until enough simulations to train the model.
            if len(self.memory.buffer) >= self.memory.batch_size:
                self.epsilon *= self.epsilon_decay

            if self.epsilon > np.random.rand():
                return random.randint(0, self.action_size-1)

        # If not acting randomly, take action with highest predicted value.
        state_batch = np.expand_dims(state, axis=0)
        predict_mask = np.ones((1, self.action_size,))
        action_qs = self.network.predict([state_batch, predict_mask])
        return np.argmax(action_qs[0])

    def learn(self):
        """Trains the Deep Q Network based on stored experiences."""
        batch_size = self.memory.batch_size
        if len(self.memory.buffer) < batch_size:
            return None

        # Obtain random mini-batch from memory.
        state_mb, action_mb, reward_mb, next_state_mb, done_mb = (
            self.memory.sample())

        # Get Q values for next_state.
        predict_mask = np.ones(action_mb.shape + (self.action_size,))
        next_q_mb = self.network.predict([next_state_mb, predict_mask])
        next_q_mb = tf.math.reduce_max(next_q_mb, axis=1)

        # Apply the Bellman Equation
        target_qs = (next_q_mb * self.memory.gamma) + reward_mb
        target_qs = tf.where(done_mb, reward_mb, target_qs)

        # Match training batch to network output:
        # target_q where action taken, 0 otherwise.
        action_mb = tf.convert_to_tensor(action_mb, dtype=tf.int32)
        action_hot = tf.one_hot(action_mb, self.action_size)
        target_mask = tf.multiply(tf.expand_dims(target_qs, -1), action_hot)

        return self.network.train_on_batch(
            [state_mb, action_hot], target_mask, reset_metrics=False
        )
