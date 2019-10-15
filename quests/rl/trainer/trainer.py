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
import json
import os
import sys
import tensorflow as tf

from . import model
from google.cloud import storage
from gym.wrappers.monitoring.video_recorder import VideoRecorder
from pyvirtualdisplay import Display

RECORDING_NAME = "recording.mp4"


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
        default=0)
    parser.add_argument(
        '--eval_rate',
        help="""While training, perform an on-policy simulation and record
        metrics to tensorboard every <record_rate> steps, 0 if never. Use
        higher values to avoid hyperparameter tuning "too many metrics"
        error""",
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
            args.memory_size, sess)
        sess.run(tf.global_variables_initializer())

        # Setup TensorBoard Writer.
        trial_id = json.loads(
            os.environ.get('TF_CONFIG', '{}')).get('task', {}).get('trial', '')
        output_path = args.job_dir if not trial_id else args.job_dir + '/'
        train_writer = tf.summary.FileWriter(output_path + "train", sess.graph)
        eval_writer = tf.summary.FileWriter(output_path + "eval", sess.graph)
        saver = tf.train.Saver()

        def _train_or_evaluate(print_score, get_summary, training=False):
            """Runs a gaming simulation and writes results for tensorboard.

            Args:
              print_score (bool): True to print a score to the console.
              get_summary (bool): True to write results for tensorboard.
              training (bool): True if the agent is training, False to eval.
            """
            reward = _play(agent, env, episode, training, print_score)
            writer = train_writer if training else eval_writer
            if training:
                get_loss = not trial_id and get_summary
                loss_summary = agent.learn(get_loss) if training else None
                if not loss_summary:
                    return

                writer.add_summary(loss_summary, global_step=episode)
                writer.flush()

            reward_summary = tf.Summary()
            reward_summary.value.add(
                tag='episode_reward', simple_value=reward)
            writer.add_summary(reward_summary, global_step=episode)
            writer.flush()

        for episode in range(args.episodes):
            get_summary = args.eval_rate and episode % args.eval_rate == 0
            print_score = (
                args.score_print_rate and
                episode % args.score_print_rate == 0)
            if args.training:
                _train_or_evaluate(print_score, get_summary, training=True)

            if not args.training or get_summary:
                _train_or_evaluate(print_score, get_summary, training=False)

        # Save the model and video.
        virtual_display = Display(visible=0, size=(1400, 900))
        virtual_display.start()
        video_recorder = VideoRecorder(env, RECORDING_NAME)
        _play(agent, env, episode, False, False, recorder=video_recorder)
        video_recorder.close()
        env.close()

        # Check if output directory is google cloud and save there if so.
        if output_path.startswith("gs://"):
            [bucket_name, blob_path] = output_path[5:].split("/", 1)
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(bucket_name)
            blob = bucket.blob(blob_path + RECORDING_NAME)
            blob.upload_from_filename(RECORDING_NAME)

        saver.save(sess, output_path + "model.ckpt")


def _play(agent, env, episode, training, print_score, recorder=None):
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
      training (bool): True is the agent is training.
      print_score (true): The episode frequency in which to print the total
        episode reward.
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
        state_prime, reward, done, info = env.step(action)
        episode_reward += reward
        agent.memory.add((state, action, reward, state_prime, done))

        if recorder:
            recorder.capture_frame()
        if done:
            if print_score:
                print(
                    'Training - ' if training else 'Evaluating - ',
                    'Episode: {}'.format(episode),
                    'Total reward: {}'.format(episode_reward),
                )
        else:
            state = state_prime  # st+1 is now our current state.
    return episode_reward


def main():
    args = _parse_arguments(sys.argv[1:])
    _run(args[0])


if __name__ == '__main__':
    main()
