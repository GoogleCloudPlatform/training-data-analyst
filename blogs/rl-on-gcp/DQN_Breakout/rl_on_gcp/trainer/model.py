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


"""Contains the Agent object which will be used for playing the game  .

This object takes the architecture, parameters and handles the training and
predicition routine.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from absl import flags
import tensorflow as tf
from .utils import *

import keras.backend as K

from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import RMSprop, Adam
from tensorflow.python.keras.layers import Input, Dense, Conv2D, Flatten, Lambda
from tensorflow.keras.callbacks import TensorBoard

from moviepy.editor import ImageSequenceClip
import gym
from gym import wrappers

# How often to write to TensorBoard.
TB_LOGGING_EPOCHS = 2000


class Agent():
  """ Agent object which initalizes and trains the keras model.
  """

  def __init__(self,
               actions,
               height=80,
               width=80,
               channels=1,
               discount=0.95,
               loss="huber",
               env="Breakout-v0",
               model_dir=None):
    """ Initializes the parameters of the model.

        Args:
          height: Height of the image
          width: Width of the image
          channels: Number of channels, history of past frame
          discount: Discount_Factor for Q Learning update
    """
    self.height = height
    self.width = width
    self.channels = channels
    self.discount = discount
    self.actions = actions
    self.env = env
    self.loss = loss
    self.epoch_num = 0
    self.model_dir = model_dir
    self.max_reward = 0
    self.cur_reward = 0
    self.reward_tensor = K.variable(value=0)
    if model_dir is not None:
      self.tbCallBack = TensorBoard(
          log_dir=model_dir,
          histogram_freq=0,
          write_graph=True,
          write_images=True)

  def create_model(
      self,
      lr,
      type="vanilla",
      rescale_value=255.0,
  ):
    """ Builds the DQN Agent architecture.

        Source:https://cs.corp.google.com/piper///depot/google3/third_party/py/
        dopamine/agents/dqn/dqn_agent.py?q=DQN&dr=CSs&l=15

        This initializes the model as per the specifications mentioned in the
        DQN paper by Deepmind. This is a sequential model implemention of
        tf.keras.  The compiled model is returned by the Method.

        Args:

        Returns:
           Model: Compiled Model

        """
    #with tf.device('/gpu:0'):
    self.image_frames = Input(shape=(self.height, self.width, self.channels))
    #self.normalize = Lambda(lambda input: input/255.0)
    self.conv1 = Conv2D(
        filters=32,
        kernel_size=(8, 8),
        strides=(4, 4),
        activation="relu",
        name="conv1")(
            Lambda(lambda input: input / float(rescale_value))(
                self.image_frames))
    self.conv2 = Conv2D(
        filters=64,
        kernel_size=(4, 4),
        strides=(2, 2),
        activation="relu",
        name="conv2")(
            self.conv1)
    self.conv3 = Conv2D(
        filters=64,
        kernel_size=(3, 3),
        strides=(1, 1),
        activation="relu",
        name="conv3")(
            self.conv2)
    self.flattened = Flatten(name="flattened")(self.conv3)
    self.fully_connected_1 = Dense(
        units=512, activation="relu", name="fully_connected_1")(
            self.flattened)
    self.q_values = Dense(
        units=self.actions, activation="linear", name="q_values")(
            self.fully_connected_1)

    self.model = Model(inputs=[self.image_frames], outputs=[self.q_values])

    self.optimizer = Adam(lr=lr)
    if self.loss == "huber":
      self.loss = huber_loss



    K.get_session().run(tf.global_variables_initializer())

    def reward(y_true, y_pred):
      return self.reward_tensor

    self.model.compile(
        optimizer=self.optimizer, loss=self.loss, metrics=["mse", reward])
    return self.model

  def batch_train(self,
                  curr_state,
                  next_state,
                  immediate_reward,
                  action,
                  done,
                  target,
                  type="Double"):
    """ Computes the TD Error for a given batch of tuples.

            Here, we randomly sample episodes from the Experience buffer and use
            this to train our model. This method computes this for a batch and
            trains the model.

           Args:
              curr_state(array): Numpy array representing an array of current
              states of game
              next_state(array): Numpy array for  immediate next state of
              the game
              action(array): List of actions taken to go from current state 
              to the next
              reward(array): List of rewards for the given transition
              done(bool): if this is a terminal state or not.
              target(keras.model object): Target network for computing TD error

        """
    if type == "Double":
      forward_action = np.argmax(self.model.predict(next_state), axis=1)
      predicted_qvalue = target.predict(next_state)  # BxN matrix
      B = forward_action.size
      forward_qvalue = predicted_qvalue[np.arange(B), forward_action]  # Bx1 vec

    elif type == "Vanilla":
      forward_qvalue = np.max(target.predict(next_state), axis=1)

    discounted_reward = (self.discount * forward_qvalue * (1 - done))
    Q_value = immediate_reward + discounted_reward
    target_values = self.model.predict(curr_state)
    target_values[range(target_values.shape[0]), action] = Q_value
    """
        for i, target in enumerate(target_values):
          target_values[i, action[i]] = Q_value[i]
        """
    callbacks = []
    # Update epoch number for TensorBoard.
    K.set_value(self.reward_tensor, self.cur_reward)
    if self.model_dir is not None and self.epoch_num % TB_LOGGING_EPOCHS == 0:
      callbacks.append(self.tbCallBack)
    self.model.fit(
        curr_state,
        target_values,
        verbose=0,
        initial_epoch=self.epoch_num,
        callbacks=callbacks,
        epochs=self.epoch_num + 1)
    self.epoch_num += 1

  def predict_action(self, state):
    """ Predict the action for a given state.

    Args:
        state(float): Numpy array
    Return:
        action(int): Discrete action to sample

    """
    #state = downsample_state(convert_greyscale(state))
    #state = np.expand_dims(state, axis=0)
    if np.ndim(state) == 3:
      state = np.expand_dims(state, axis=0)
    return np.argmax(self.model.predict(state))

  def play(self, env, directory, mode):
    """ Returns the total reward for an episode of the game."""
    steps = []
    state = env.reset()
    done = False
    tot_reward = 0
    actions = [0] * self.actions
    while not done:
      if mode != "Train":
        s = env.render("rgb_array")
        steps.append(s)

      action = self.predict_action(state)
      actions[action] += 1
      state, reward, done, _ = env.step(action)
      tot_reward += reward
    self.cur_reward = tot_reward
    if mode != "Train" and tot_reward > self.max_reward:
      print("New high reward: ", tot_reward)
      clip = ImageSequenceClip(steps, fps=30)
      clip.write_gif("~/breakout.gif", fps=30)
      self.max_reward = tot_reward

    print("ACTIONS TAKEN", actions)
    return tot_reward
