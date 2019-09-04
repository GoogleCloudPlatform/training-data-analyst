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


# Create agent components
def deep_q_network(state_shape, action_size, learning_rate, hidden_neurons):
    """Creates a Deep Q Network to emulate Q-learning.

    Creates a two hidden-layer Deep Q Network. Similar to a typical nueral
    network, the loss function is altered to reduce the difference between
    predicted Q-values and Target Q-values.

    Args:
        space_shapes ():
        learning_rate (float): the nueral network's learning rate.
        hidden_neurons (int): the number of neurons to use per hidden
            layer.
    """
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(
            hidden_neurons, activation='relu', input_shape=state_shape),
        tf.keras.layers.Dense(hidden_neurons, activation='relu'),
        tf.keras.layers.Dense(action_size)
    ])
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
            experience: a (state, action, state_prime, reward, done) tuple.
        """
        self.buffer.append(experience)

    def sample(self):
        """Uniformally selects from the replay memory buffer.

        Uniformally and randomly selects experiences to train the nueral
        network on. Transposes the experiences to allow batch math on
        the experience components.

        Returns:
            (list): A list of lists with structure [
                [states], [actions], [state_primes], [rewards], [dones]
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


# Create agent
class Agent():
    """Sets up a reinforcement learning agent to play in a game environment."""
    def __init__(self, network, memory, epsilon_decay, action_size):
        """Initializes the agent with DQN and memory sub-classes.

        Args:
            network:
            memory:
            epsilon_decay (float): The rate at which to decay random actions.
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
        action_qs = self.network.predict(state_batch)
        return np.argmax(action_qs)

    def learn(self):
        """Trains the Deep Q Network based on stored experiences.

        Returns:
            None or a Tensorboard Summary for the training loss.
        """
        batch_size = self.memory.batch_size
        if len(self.memory.buffer) < batch_size:
            return None

        # Obtain random mini-batch from memory.
        states_mb, actions_mb, rewards_mb, states_prime_mb, dones_mb = (
            self.memory.sample())

        # Get Q values for next_state.
        qs_state_prime = self.network.predict(states_prime_mb)
        qs_state_prime = tf.math.reduce_max(qs_state_prime, axis=1)

        target_qs = (qs_state_prime * self.memory.gamma) + rewards_mb
        target_qs = tf.where(dones_mb, rewards_mb, target_qs)
        actions_hot = tf.one_hot(actions_mb, self.action_size)
        actions_mask = tf.greater(actions_hot, 0)
        target_mask = tf.multiply(tf.expand_dims(target_qs, -1), actions_hot)

        qs_current_state = self.network.predict(states_mb, steps=1)
        training_feed = tf.where(actions_mask, target_mask, qs_current_state)

        self.network.fit(
            states_mb, training_feed, batch_size=batch_size, epochs=1,
            steps_per_epoch=1, verbose=0
        )

        return None
