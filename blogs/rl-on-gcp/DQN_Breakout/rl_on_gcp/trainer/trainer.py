"""TODO(praneetdutta): DO NOT SUBMIT without one-line documentation for train
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicableQQlaw or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .stack_frame_env import StackFrameEnv

from absl import app
from absl import flags
import tensorflow as tf
from tensorflow.keras import models
import random
import gym
import sys
from .model import Agent
from .utils import *
from .buffer import ExpBuffer
import argparse
import datetime
import os

SAVE_STEPS_FACTOR = 5
DISPLAY_RESULTS = 100

def _run(args):
  """ TODO(praneetdutta): Formalize train sub-routine
  """
  with tf.Session() as sess:
    env = gym.make(args[0].environment)
    env = StackFrameEnv(env, args[0].frame_stack,
     args[0].img_height, args[0].img_width)
    state = env.reset()
    num_actions = env.action_space.n
    if args[0].mode == 'Train':
      # Add timestamp; important for HP tuning so models don't clobber each
      # other.
      model_dir = hp_directory(args[0].model_dir)
    else:
      model_dir = args[0].model_dir
    agent = Agent(
        height=args[0].img_height,
        width=args[0].img_width,
        actions=env.action_space.n,
        channels=args[0].frame_stack,
        model_dir=model_dir,
        discount=args[0].discount_factor)
    agent.create_model(lr=args[0].learning_rate)
    print ("STARTING...")

    if not os.path.exists(model_dir) and args[0].save_model:
      os.makedirs(model_dir)
    print("MODEL WILL BE STORED AT: ", model_dir)
    target_agent = Agent(height=args[0].img_height, width=args[0].img_width,
     actions=env.action_space.n, channels=args[0].frame_stack)
    target_agent.create_model(args[0].learning_rate)
    target_network  = target_agent.model
    target_network.set_weights(agent.model.get_weights())
    if args[0].mode != 'Train':
      trained_model_path = args[0].load_model
      try:
        agent.model.load_weights(trained_model_path)
      except:
        print('{} is not a valid .h5 model.'.format(trained_model_path))
    eta = args[0].init_eta
    Buffer = ExpBuffer(max_size=args[0].buffer_size,
      min_size=args[0].start_train)
    episode_reward, episode_number, done = 0, 0, False
    episode_run = True

    for curr_step in range(args[0].steps):
      if (episode_number % DISPLAY_RESULTS == 0 and
          episode_run) or args[0].mode != 'Train':
        episode_reward = agent.play(env, model_dir, args[0].mode)
        print('CURRENT STEP: {}, EPISODE_NUMBER: {}, EPISODE REWARD: {},'
              'EPSILON: {}'.format(curr_step, episode_number, episode_reward,
                                   eta))
        episode_run = False


      if args[0].mode == 'Train':
        eta = anneal_exploration(eta, curr_step, args[0].steps / 10.0,
                                 args[0].start_train, args[0].init_eta,
                                 args[0].min_eta, 'linear')

        if eta > np.random.rand() or curr_step < args[0].start_train:
          action = env.action_space.sample()
        else:
          action = agent.predict_action(state)

        next_state, reward, done, info = env.step(action)
        Buffer.add_exp([state, next_state, reward, action, done])
        ready_to_update_model = curr_step > args[0].start_train and len(
            Buffer.buffer) > Buffer.min_size
        if ready_to_update_model:
          exp_state, exp_next_state, exp_reward, exp_action, exp_done = Buffer.sample_experiences(
              args[0].batch_size)
          agent.batch_train(exp_state, exp_next_state, exp_reward, exp_action,
                            exp_done, target_network, args[0].Q_learning)
          if curr_step % args[0].update_target == 0:
            target_network.set_weights(agent.model.get_weights())
          if curr_step % (SAVE_STEPS_FACTOR *
                          args[0].update_target) == 0 and args[0].save_model:
            print('SAVING MODEL AT STEP: ', curr_step)
            models.save_model(
                agent.model,
                model_dir + 'model_' + str(episode_number) + '_.h5')
        #Resets state
        if done or args[0].mode != 'Train':
          episode_number += 1
          episode_run = True
          state = env.reset()
        else:
          state = next_state


def _parse_arguments(argv):
  """Parse command-line arguments."""

  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--img_width',
      help='Width of desired image observation',
      type=float,
      default=128)
  parser.add_argument(
      '--img_height',
      help='Height of desired image observation',
      type=float,
      default=128)
  parser.add_argument(
      '--environment',
      help='Atari Game Environment to be used.',
      type=str,
      default='Breakout-v0')
  parser.add_argument(
      '--frame_stack',
      help='Number of frames to stack ',
      type=float,
      default=4)
  parser.add_argument(
      '--steps',
      help='Number of steps for the agent to play the game',
      type=int,
      default=5000000)
  parser.add_argument(
      '--start_train',
      help='Number of steps after which to start training',
      type=int,
      default=5000)
  parser.add_argument(
      '--update_target',
      help='Number of steps after which to update the target network',
      type=int,
      default=1000)
  parser.add_argument(
      '--buffer_size',
      help='Size of the experience buffer',
      type=int,
      default=200000)
  parser.add_argument(
      '--mode',
      help='Whether we are training the agent or playing the game',
      type=str,
      default="Train")
  parser.add_argument(
      '--init_eta', help='Epsilon for taking actions', type=float, default=0.95)
  parser.add_argument(
      '--model_dir',
      help='Directory where to save the given model',
      type=str,
      default='models/')
  parser.add_argument(
      '--save_model',
      help='Whether to save the model',
      type=bool,
      default= False)
  parser.add_argument(
      '--batch_size',
      help='Batch size for sampling and training model',
      type=int,
      default=32)
  parser.add_argument(
      '--learning_rate',
      help='Learning rate for for agent and target network',
      type=float,
      default=0.00025)
  parser.add_argument(
      '--Q_learning',
      help='Type of Q Learning to be implemented',
      type=str,
      default= "Double")
  parser.add_argument(
      '--min_eta', help='Lower bound of epsilon', type=float, default=0.1)
  parser.add_argument(
      '--discount_factor',
      help='Discount Factor for TD Learning',
      type=float,
      default=0.95)
  parser.add_argument(
      '--load_model', help='Loads the model', type=str, default=None)
  return parser.parse_known_args(argv)


def main():
  args = _parse_arguments(sys.argv[1:])
  _run(args)

if __name__ == '__main__':
  main()
