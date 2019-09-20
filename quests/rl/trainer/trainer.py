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

"""A training script to train an RL agent in an OpenAI Gym game."""

import argparse
import json
import os
import sys

sys.path.append('/root/.local/lib/python3.6/site-packages')

from google.cloud import storage
import gym
from gym.wrappers.monitoring.video_recorder import VideoRecorder
import hypertune
from pyvirtualdisplay import Display
import tensorflow as tf

from . import model

RECORDING_NAME = "recording.mp4"
sys.stdout.flush()


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
        default=400)
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
        '--training',
        help='True for the model to train, False for the model to evaluate',
        type=bool,
        default=True)
    parser.add_argument(
        '--job-dir',
        help='Directory where to save the given model',
        type=str,
        default='models/')
    parser.add_argument(
        '--score_print_rate',
        help='How often to print the score, 0 if never',
        type=int,
        default=20)
    parser.add_argument(
        '--eval_rate',
        help="""While training, perform an on-policy simulation and record
        metrics to tensorboard every <record_rate> steps, 0 if never. Use
        higher values to avoid hyperparameter tuning "too many metrics"
        error""",
        type=int,
        default=400)
    return parser.parse_known_args(argv)


def _run(args):
    """Sets up and runs the gaming simulation.

    Initializes TensorFlow, the training agent, and the game environment.
    The agent plays the game from the starting state for a number of
    episodes set by the user.

    Args:
      args: The arguments from the command line parsed by_parse_arguments.
    """
    graph = tf.Graph()
    with graph.as_default():
        env = gym.make(args.game)
        agent = _create_agent(env, args)

        # Setup TensorBoard Writer.
        trial_id = json.loads(
            os.environ.get('TF_CONFIG', '{}')).get('task', {}).get('trial', '')
        output_path = args.job_dir if not trial_id else args.job_dir + '/'
        saver = tf.compat.v1.train.Saver()
        hpt = hypertune.HyperTune()

        def _train_or_evaluate(print_score, get_summary, training=False):
            """Runs a gaming simulation and writes results for tensorboard.

            Args:
              print_score (bool): True to print a score to the console.
              get_summary (bool): True to write results for tensorboard.
              training (bool): True if the agent is training, False to eval.
            """
            reward = _play(agent, env, training)
            if print_score:
                print(
                    'Training - ' if training else 'Evaluating - ',
                    'Episode: {}'.format(episode),
                    'Total reward: {}'.format(reward),
                )

            if training:
                agent.learn()
                return

            hpt.report_hyperparameter_tuning_metric(
                hyperparameter_metric_tag='episode_reward',
                metric_value=reward,
                global_step=episode)

        for episode in range(1, args.episodes+1):
            get_summary = args.eval_rate and episode % args.eval_rate == 0
            print_score = (
                args.score_print_rate and
                episode % args.score_print_rate == 0)
            if args.training:
                _train_or_evaluate(print_score, get_summary, training=True)

            if not args.training or get_summary:
                _train_or_evaluate(print_score, get_summary)

        _record_video(env, agent, output_path)


def _play(agent, env, training, recorder=None):
    """Plays through one episode of the game.

    Initializes TensorFlow, the training agent, and the game environment.
    The agent plays the game from the starting state for a number of
    episodes set by the user.

    Args:
      agent: The actor learning to play in the given environment.
      env: The environment for the agent to act in. This code is intended for
        use with OpenAI Gym, but the user can alter the code to provide their
        own environment.
      training (bool): True is the agent is training.
      recorder (optional): A gym video recorder object to save the simulation
        to a movie.
    """
    episode_reward = 0  # The total reward for an episode.
    state = env.reset()  # Set up Environment and get start state.
    done = False
    if recorder:
        recorder.capture_frame()

    while not done:
        action = agent.act(state, training)
        state_prime, reward, done, _ = env.step(action)
        episode_reward += reward
        agent.memory.add((state, action, reward, state_prime, done))

        if recorder:
            recorder.capture_frame()
        state = state_prime  # st+1 is now our current state.
    return episode_reward


def _create_agent(env, args):
    """Creates a Reinforcement Learning agent.

    Args:
      env: The environment for the agent to act in.
      args: The arguments from the command line parsed by_parse_arguments.

    Returns:
      An RL agent.
    """
    space_shape = env.observation_space.shape
    action_size = env.action_space.n
    network = model.deep_q_network(
        space_shape, action_size, args.learning_rate, args.hidden_neurons)
    memory = model.Memory(args.memory_size, args.memory_batch_size, args.gamma)
    return model.Agent(network, memory, args.explore_decay, action_size)


def _record_video(env, agent, output_path):
    """Records a video of an agent playing a gaming simulation.

    Args:
      env: The environment for the agent to act in.
      agent: An RL agent created by _create_agent.
      output_path (str): The directory path of where to save the recording.
    """
    virtual_display = Display(visible=0, size=(1400, 900))
    virtual_display.start()
    video_recorder = VideoRecorder(env, RECORDING_NAME)
    _play(agent, env, False, recorder=video_recorder)
    video_recorder.close()
    virtual_display.stop()
    env.close()

    # Check if output directory is google cloud and save there if so.
    if output_path.startswith("gs://"):
        [bucket_name, blob_path] = output_path[5:].split("/", 1)
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_path + RECORDING_NAME)
        blob.upload_from_filename(RECORDING_NAME)


def main():
    """Parses command line arguments and kicks off the gaming simulation."""
    args = _parse_arguments(sys.argv[1:])
    _run(args[0])


if __name__ == '__main__':
    print("hi")
    main()
