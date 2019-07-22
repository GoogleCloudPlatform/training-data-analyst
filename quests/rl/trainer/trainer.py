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

import argparse
import gym
import numpy as np
import sys
import tensorflow as tf

from . import model


def _parse_arguments(argv):
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--game',
        help='Which open ai gym game to play',
        type=str,
        default='CartPole-v0')
    parser.add_argument(
        '--episodes',
        help='The number of episodes to simulate',
        type=int,
        default=500)
    parser.add_argument(
        '--learning_rate',
        help='Learning rate for the nueral network',
        type=float,
        default=0.002)
    parser.add_argument(
        '--hidden_neurons',
        help='The number of nuerons to use per layer',
        type=int,
        default=50)
    parser.add_argument(
        '--gamma',
        help='The gamma or "discount" factor to discount future states',
        type=float,
        default=0.9)
    parser.add_argument(
        '--explore_decay',
        help='The rate at which to decay the probability of a random action',
        type=float,
        default=0.01)
    parser.add_argument(
        '--memory_size',
        help='Size of the memory buffer',
        type=int,
        default=100000)
    parser.add_argument(
        '--memory_batch_size',
        help='The amount of memories to sample from the buffer while training',
        type=int,
        default=64)
    parser.add_argument(
        '--training_mode',
        help='True for the model to train, False for the model to evaluate',
        type=bool,
        default=True)
    parser.add_argument(
        '--model_path',
        help='Directory where to save the given model',
        type=str,
        default='models/')
    parser.add_argument(
        '--save_model',
        help='Whether to save the model',
        type=bool,
        default=True)
    parser.add_argument(
        '--score_print_rate',
        help='How often to print the score, 0 if never',
        type=int,
        default=0)
    parser.add_argument(
        '--render_rate',
        help='How often to render an episode, 0 if never',
        type=int,
        default=0)
    parser.add_argument(
        '--record_rate',
        help="""Record metrics to tensorboard every <record_rate> steps, 0 if
        never. Use higher values to avoid hyperparameter tuning
        "too many metrics" error""",
        type=int,
        default=100)
    return parser.parse_known_args(argv)


def _run(args):
    """Sets up and runs the gaming simulation.

    Initializes TensorFlow, the training agent, and the game environment.
    The agent plays the game from the starting state for a number of
    episodes set by the user.

    Args:
      args (dict): The arguments from the command line parsed by
        _parse_arguments.
    """
    with tf.Session() as sess:
        env = gym.make(args.game)
        space_size = env.observation_space.shape
        action_size = env.action_space.n
        agent = model.Agent(
            space_size, action_size, args.learning_rate, args.hidden_neurons,
            args.gamma, args.explore_decay, args.memory_batch_size,
            args.memory_size, args.training_mode, sess, args.model_path)

        # Initialize the variables
        sess.run(tf.global_variables_initializer())
        saver = tf.train.Saver()

        for episode in range(args.episodes):
            _play(
                agent, env, episode, args.render_rate, args.score_print_rate,
                args.record_rate)

        # Save the model
        save_path = saver.save(sess, args.model_path)


def _play(agent, env, episode, render_rate, score_print_rate, record_rate):
    """Plays through one episode of the game.

    Initializes TensorFlow, the training agent, and the game environment.
    The agent plays the game from the starting state for a number of
    episodes set by the user.

    Args:
      agent: The actor learning to play in the given environment.
      env: The environment for the agent to act in. This code is intended for
        use with OpenAI Gym, but the user can alter the code to provide their
        own environment.
      episode (int): The current number of simulaions the agent has completed.
      render_rate (int): The episode frequency in which to render the game
        being played by the agent.
      score_print_rate (int): The episode frequency in which to print the total
        episode reward.
      record_rate (int): The episode frequency in which to record the episode
        reward into tensorboard.
    """
    episode_reward = 0  # The total reward for an episode.
    state = env.reset()  # Set up Environment and get start state.
    done = False

    while not done:
        action = agent.act(state)
        state_prime, reward, done, info = env.step(action)
        episode_reward += reward
        agent.memory.add((state, action, reward, state_prime, done))

        # Render only enough to "check in" on the agent to speed up training.
        if render_rate and episode % render_rate == 0:
            env.render()

        if done:
            if score_print_rate and episode % score_print_rate == 0:
                print(
                    'Training: {}'.format(agent.train),
                    'Episode: {}'.format(episode),
                    'Total reward: {}'.format(episode_reward),
                )
        else:
            state = state_prime  # st+1 is now our current state.

    if agent.train:
        # TODO: Eval every x steps instead of recording training rewards.
        tensorboard_write = episode % record_rate == 0
        agent.learn(episode_reward, tensorboard_write)


def main():
    args = _parse_arguments(sys.argv[1:])
    _run(args[0])

if __name__ == '__main__':
    main()
