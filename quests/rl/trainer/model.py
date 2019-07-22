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

import json
import numpy as np
import os
import random
import tensorflow as tf

from collections import deque
from enum import Enum


# Create agent components
class DQNetwork():
    def __init__(
        self, state_size, action_size, learning_rate, hidden_nuerons,
            name='DQNetwork'):
        """Creates a Deep Q Network to emulate Q-learning.

        Creates a two hidden-layer Deep Q Network. Similar to a typical nueral
        network, the loss function is altered to reduce the difference between
        predicted Q-values and Target Q-values.

        Args:
            state_size (int): the number of parameters used to define the state
                the agent is in.
            action_size (int): the number of different actions the agent can
                take.
            learning_rated (float): the nueral network's learning rate.
            hidden_nuerons (int): the number of nuerons to use per hidden
                layer.
            name (str): What to call the network, as shown in tensorboard.
        """
        with tf.variable_scope(name):
            self.states = tf.placeholder(
                tf.float32, shape=((None,) + state_size), name='states')
            self.actions = tf.placeholder(
                tf.int32, shape=(None), name='actions')

            # For tracking the reward in tensorboard and vizier
            self.episode_reward = tf.placeholder(
                dtype=tf.float32, shape=[], name='episode_reward')
            tf.summary.scalar('episode_reward', self.episode_reward)

            # target_Q is R(s,a) + ymax Qhat(s', a')
            self.target_Q = tf.placeholder(tf.float32, [None], name="target")

            # TODO(ddetering): Switch to keras.
            self.fully_connected_1 = tf.layers.dense(
                inputs=self.states,
                units=hidden_nuerons,
                activation=tf.nn.relu,
                name="fully_connected_1")

            self.fully_connected_2 = tf.layers.dense(
                inputs=self.fully_connected_1,
                units=hidden_nuerons,
                activation=tf.nn.relu,
                name="fully_connected_2")

            self.output = tf.layers.dense(
                inputs=self.fully_connected_2,
                units=action_size,
                activation=None)

            # Hot encode and multiply across to select Q value for an action.
            self.actions_hot = tf.one_hot(self.actions, action_size)
            # Q is our predicted Q value.
            self.Q = tf.reduce_sum(
                tf.multiply(self.output, self.actions_hot), axis=1)

            # The loss is the difference between predicted Q_values and
            # the Q_target Sum(Qtarget - Q)^2
            self.loss = tf.reduce_mean(tf.square(self.target_Q - self.Q))
            self.optimizer = (
                tf.train.RMSPropOptimizer(learning_rate).minimize(self.loss))
            tf.summary.scalar("loss", self.loss)  # Track in Tensorboard.


class Memory():
    """Sets up a memory replay buffer for a Deep Q Network.

    A simple memory buffer for a DQN. This one randomly selects state
    transitions with uniform probability, but research has gone into
    other methods. For instance, a weight could be given to each memory
    depending on how big of a difference there is between predicted Q values
    and target Q values.
    """
    def __init__(self, memory_size):
        self.buffer = deque(maxlen=memory_size)

    def add(self, experience):
        """Adds an experience into the memory buffer.

        Args:
            experience: a (state, action, state_prime, reward, done) tuple.
        """
        self.buffer.append(experience)

    def sample(self, batch_size):
        """Uniformally selects from the replay memory buffer.

        Uniformally and randomly selects experiences to train the nueral
        network on. Transposes the experiences to allow batch math one
        the experience components.
        
        Args:
            batch_size (int): the number of experiences to sample

        Returns:
            (list): A list of lists with structure [
                [states], [actions], [state_primes], [rewards], [dones]
            ]
        """
        buffer_size = len(self.buffer)
        index = np.random.choice(
            np.arange(buffer_size), size=batch_size, replace=False)

        # Columns have different data types, so numpy array would be awkward.
        return np.array([self.buffer[i] for i in index]).T.tolist()


# Create agent
class Agent():
    """Sets up a reinforcement learning agent to play in a game environment."""
    def __init__(
            self, state_size, action_size, learning_rate, hidden_nuerons,
            gamma, epsilon_decay, memory_batch_size, memory_size, train,
            tensorflow_session, output_path):
        """Initializes the agent with DQN and memory sub-classes.

        Args:
            state_size (tuple of ints): The shape and size of the parameters
                outputed by the game environment.
            action_size (int): The number of actions the agent may choose from.
            learning_rate (int): The nueral network learning rate.
            hidden_nuerons (int): The number of hidden nuerons per layer of
                the DQN.
            gamma (float): The "discount rate" used to assess Q values.
            epsilon_decay (float): The rate at which to decay random actions.
            memory_batch_size (int): The number of experiences to pull from the
                replay memory during training.
            memory_size (int): The maximum number of experinces the memory 
                buffer can hold.
            train (bool): True if the agent is in training mode.
            tensorflow_session: The Tensorflow session the simulation is taking
                place in.
            output_path (str): The directory to output TensorBoard summaries.
        """
        self.action_size = action_size
        self.brain = DQNetwork(
            state_size, action_size, learning_rate, hidden_nuerons)
        self.memory = Memory(memory_size)
        self.session = tensorflow_session
        self.train = train
        self.memory_batch_size = memory_batch_size
        self.gamma = gamma
        self.epsilon = 1  # The chance to take a random action.
        self.epsilon_decay = epsilon_decay

        # Setup TensorBoard Writer.
        trial_id = json.loads(
            os.environ.get('TF_CONFIG', '{}')).get('task', {}).get('trial', '')
        summary_path = os.path.join(output_path, trial_id)
        self.writer = tf.summary.FileWriter(summary_path, self.session.graph)

    def act(self, state):
        """Selects an action for the agent to take given a game state.

        Args:
            state (list of numbers): The state of the environment to act on.

        Returns:
            (int) The index of the action to take.
        """
        if self.train:
            # Random actions until enough simulations to train the model.
            if len(self.memory.buffer) >= self.memory_batch_size:
                self.epsilon *= self.epsilon_decay

            if (self.epsilon > np.random.rand()):
                return random.randint(0, self.action_size-1)

        # If not acting randomly, take action with highest predicted value.
        Qs = self.session.run(
            self.brain.output, feed_dict={self.brain.states: [state]})
        return np.argmax(Qs)

    def learn(self, episode_reward, tensorboard_write):
        """Trains the Deep Q Network based on stored experiences.
        Args:
            episode_reward (number): The latest episode reward for tracking.
            tensorboard_write (bool): True if writing to tensorboard.
        """
        if len(self.memory.buffer) < self.memory_batch_size:
            return np.inf
        brain = self.brain

        # Obtain random mini-batch from memory.
        states_mb, actions_mb, rewards_mb, states_prime_mb, dones_mb = (
            self.memory.sample(self.memory_batch_size))

        # Get Q values for next_state.
        Qs_next_state = self.session.run(
            brain.output, feed_dict={brain.states: states_prime_mb})

        # Set Q_target = r if the episode ends at s+1.
        # Otherwise set Q_target = r + gamma*maxQ(s', a').
        target_Qs_batch = np.array([
            rewards_mb[i] if dones_mb[i]
            else rewards_mb[i] + self.gamma * np.max(Qs_next_state[i])
            for i in range(len(rewards_mb))
        ])

        targets_mb = np.array(target_Qs_batch)
        model_feed = {
            brain.states: states_mb,
            brain.target_Q: targets_mb,
            brain.actions: actions_mb,
            brain.episode_reward: episode_reward
        }

        loss, _ = self.session.run(
            [brain.loss, brain.optimizer], feed_dict=model_feed)

        # Merge summaries for tensorboard.
        if tensorboard_write:
            summary = self.session.run(
                tf.summary.merge_all(), feed_dict=model_feed)
            self.writer.add_summary(summary)
