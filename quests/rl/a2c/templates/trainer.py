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

from google.cloud import storage
import gym
from gym.wrappers.monitoring.video_recorder import VideoRecorder
import hypertune
import tensorflow as tf
from tensorflow.keras.callbacks import TensorBoard

from . import model

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
        default=2000)
    parser.add_argument(
        '--learning_rate',
        help='Learning rate for the nueral network',
        type=float,
        default=0.0005)
    parser.add_argument(
        '--critic_weight',
        help='Learning rate for the nueral network',
        type=float,
        default=0.95)
    parser.add_argument(
        '--hidden_neurons',
        help='The number of nuerons to use per layer',
        type=int,
        default=128)
    parser.add_argument(
        '--gamma',
        help='The gamma or "discount" factor to discount future states',
        type=float,
        default=0.995)
    parser.add_argument(
        '--batch_size',
        help='How often to print the score, 0 if never',
        type=int,
        default=32)
    parser.add_argument(
        '--entropy',
        help='How often to print the score, 0 if never',
        type=float,
        default=0.0001)
    parser.add_argument(
        '--print_rate',
        help='How often to print the score, 0 if never',
        type=int,
        default=0)
    parser.add_argument(
        '--job-dir',
        help='Directory where to save the given model',
        type=str,
        default='models/')
    parser.add_argument(
        '--eval_rate',
        help="""While training, perform an on-policy simulation and record
        metrics to tensorboard every <record_rate> steps, 0 if never. Use
        higher values to avoid hyperparameter tuning "too many metrics"
        error""",
        type=int,
        default=50)
    return parser.parse_known_args(argv)


def _run(game, network_params, memory_params, ops):
    """Sets up and runs the gaming simulation.

    Initializes TensorFlow, the training agent, and the game environment.
    The agent plays the game from the starting state for a number of
    episodes set by the user.

    Args:
      args: The arguments from the command line parsed by_parse_arguments.
    """
    # Setup TensorBoard Writer.
    trial_id = json.loads(
        os.environ.get('TF_CONFIG', '{}')).get('task', {}).get('trial', '')
    output_path = ops.job_dir if not trial_id else ops.job_dir + '/'
    tensorboard = TensorBoard(log_dir=output_path)
    hpt = hypertune.HyperTune()

    graph = tf.Graph()
    with graph.as_default():
        env = gym.make(game)
        agent = _create_agent(env, network_params, memory_params)
        rewards = []
        tensorboard.set_model(agent.policy)

        def _train_or_evaluate(print_score, training=False):
            """Runs a gaming simulation and writes results for tensorboard.

            Args:
                print_score (bool): True to print a score to the console.
                training (bool): True if the agent is training, False to eval.

            Returns:
                loss if training, else reward for evaluating.
            """
            reward = _play(agent, env, training)
            if print_score:
                print(
                    'Train - ',
                    'Episode: {}'.format(episode),
                    'Total reward: {}'.format(reward),
                )
            return reward

        for episode in range(1, ops.episodes+1):
            print_score = ops.print_rate and episode % ops.print_rate == 0
            get_summary = ops.eval_rate and episode % ops.eval_rate == 0
            rewards.append(_train_or_evaluate(print_score, training=True))

            if get_summary:
                avg_reward = sum(rewards) / len(rewards)
                summary =  {'eval_reward': avg_reward}
                tensorboard.on_epoch_end(episode, summary)
                hpt.report_hyperparameter_tuning_metric(
                    hyperparameter_metric_tag='avg_reward',
                    metric_value=avg_reward,
                    global_step=episode)
                print(
                    'Eval - ',
                    'Episode: {}'.format(episode),
                    'Average Reward: {}'.format(avg_reward),
                )
                rewards = []

        tensorboard.on_train_end(None)
        _record_video(env, agent, output_path)
        agent.policy.save(output_path, save_format='tf')


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
      training (bool): True if the agent is training.
      recorder (optional): A gym video recorder object to save the simulation
        to a movie.
    """
    episode_reward = 0  # The total reward for an episode.
    state = env.reset().tolist()  # Set up Environment and get start state.
    done = False
    if recorder:
        recorder.capture_frame()

    while not done:
        action = agent.act(state)
        state_prime, reward, done, _ = env.step(action)
        episode_reward += reward
        next_value = agent.critic.predict([[state_prime]])
        agent.memory.add((state, action, reward, done, next_value))

        if training and agent.memory.check_full():
            agent.learn()

        if recorder:
            recorder.capture_frame()
        state = state_prime  # st+1 is now our current state.

    return episode_reward


def _create_agent(env, network_params, memory_params):
    """Creates a Reinforcement Learning agent.

    Args:
      env: The environment for the agent to act in.
      network_params: Parameters to build actor-critic neural networks.
      memory_params: Parameters to an actor-critic memory buffer.

    Returns:
      An RL agent.
    """
    space_shape = env.observation_space.shape[0]
    action_size = env.action_space.n
    actor, critic, policy = model.build_networks(
        space_shape, action_size, *network_params)
    memory = model.Memory(*memory_params)
    return model.Agent(actor, critic, policy, memory, action_size)


def _record_video(env, agent, output_path):
    """Records a video of an agent playing a gaming simulation.

    Args:
      env: The environment for the agent to act in.
      agent: An RL agent created by _create_agent.
      output_path (str): The directory path of where to save the recording.
    """
    video_recorder = VideoRecorder(env, RECORDING_NAME)
    _play(agent, env, False, recorder=video_recorder)
    video_recorder.close()
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
    args = _parse_arguments(sys.argv[1:])[0]
    network_params = (
        args.learning_rate, args.critic_weight, args.hidden_neurons, args.entropy)
    memory_params = (args.gamma, args.batch_size)
    ops = argparse.Namespace(**{
        'job_dir': args.job_dir,
        'episodes': args.episodes,
        'print_rate': args.print_rate,
        'eval_rate': args.eval_rate
    })
    _run(args.game, network_params, memory_params, ops)


if __name__ == '__main__':
    main()
