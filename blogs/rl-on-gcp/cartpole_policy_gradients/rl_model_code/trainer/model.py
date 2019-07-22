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
"""Simple policy gradients for Reinforcement learning on Google Cloud.

Also includes code for hyperparameter tuning. Adapted from:
https://github.com/ageron/handson-ml/blob/master/16_reinforcement_learning.ipynb
"""

import json
import os

import gym
import numpy as np
import tensorflow as tf

tf.reset_default_graph()

# task.py arguments.
N_GAMES_PER_UPDATE = None
DISCOUNT_RATE = None
N_HIDDEN = None
LEARNING_RATE = None

# Currently hardcoded.
n_max_steps = 1000
n_iterations = 30
save_iterations = 5

# For cartpole.
env = gym.make('CartPole-v0')
n_inputs = 4
n_outputs = 1


def discount_rewards(rewards, discount_rate):
  discounted_rewards = np.zeros(len(rewards))
  cumulative_rewards = 0
  for step in reversed(range(len(rewards))):
    cumulative_rewards = rewards[step] + cumulative_rewards * discount_rate
    discounted_rewards[step] = cumulative_rewards
  return discounted_rewards


def discount_and_normalize_rewards(all_rewards, discount_rate):
  all_discounted_rewards = [
      discount_rewards(rewards, discount_rate) for rewards in all_rewards
  ]
  flat_rewards = np.concatenate(all_discounted_rewards)
  reward_mean = flat_rewards.mean()
  reward_std = flat_rewards.std()
  return [(discounted_rewards - reward_mean) / reward_std
          for discounted_rewards in all_discounted_rewards]


def hp_directory(model_dir):
  """If running a hyperparam job, create subfolder name with trial ID.

  If not running a hyperparam job, just keep original model_dir.
  """
  trial_id = json.loads(os.environ.get('TF_CONFIG', '{}')).get('task', {}).get(
      'trial', '')
  return os.path.join(model_dir, trial_id)


# Play games and train agent. Or evaluate and make gifs.
def run(outdir, train_mode):

  # Build network.
  initializer = tf.keras.initializers.VarianceScaling()
  X = tf.placeholder(tf.float32, shape=[None, n_inputs])
  hidden = tf.layers.dense(
      X, N_HIDDEN, activation=tf.nn.elu, kernel_initializer=initializer)
  logits = tf.layers.dense(hidden, n_outputs)
  outputs = tf.nn.sigmoid(logits)  # probability of action 0 (left)
  p_left_and_right = tf.concat(axis=1, values=[outputs, 1 - outputs])
  action = tf.multinomial(tf.log(p_left_and_right), num_samples=1)

  # Optimizer, gradients.
  y = 1. - tf.to_float(action)
  cross_entropy = tf.nn.sigmoid_cross_entropy_with_logits(
      labels=y, logits=logits)
  optimizer = tf.train.AdamOptimizer(LEARNING_RATE)
  grads_and_vars = optimizer.compute_gradients(cross_entropy)
  gradients = [grad for grad, variable in grads_and_vars]
  gradient_placeholders = []
  grads_and_vars_feed = []
  for grad, variable in grads_and_vars:
    gradient_placeholder = tf.placeholder(tf.float32, shape=grad.get_shape())
    gradient_placeholders.append(gradient_placeholder)
    grads_and_vars_feed.append((gradient_placeholder, variable))
  training_op = optimizer.apply_gradients(grads_and_vars_feed)

  # For TensorBoard.
  episode_reward = tf.placeholder(dtype=tf.float32, shape=[])
  tf.summary.scalar('reward', episode_reward)

  init = tf.global_variables_initializer()
  saver = tf.train.Saver()

  if train_mode:
    hp_save_dir = hp_directory(outdir)
    with tf.Session() as sess:
      init.run()
      # For TensorBoard.
      print('hp_save_dir')
      train_writer = tf.summary.FileWriter(hp_save_dir, sess.graph)
      for iteration in range(n_iterations):
        all_rewards = []
        all_gradients = []
        for game in range(N_GAMES_PER_UPDATE):
          current_rewards = []
          current_gradients = []
          obs = env.reset()
          for step in range(n_max_steps):
            action_val, gradients_val = sess.run(
                [action, gradients], feed_dict={X: obs.reshape(1, n_inputs)})
            obs, reward, done, info = env.step(action_val[0][0])
            current_rewards.append(reward)
            current_gradients.append(gradients_val)
            if done:
              break
          all_rewards.append(current_rewards)
          all_gradients.append(current_gradients)
        avg_reward = np.mean(([np.sum(r) for r in all_rewards]))

        print('\rIteration: {}, Reward: {}'.format(
            iteration, avg_reward, end=''))
        all_rewards = discount_and_normalize_rewards(
            all_rewards, discount_rate=DISCOUNT_RATE)
        feed_dict = {}
        for var_index, gradient_placeholder in enumerate(gradient_placeholders):
          mean_gradients = np.mean([
              reward * all_gradients[game_index][step][var_index]
              for game_index, rewards in enumerate(all_rewards)
              for step, reward in enumerate(rewards)
          ],
                                   axis=0)
          feed_dict[gradient_placeholder] = mean_gradients
        sess.run(training_op, feed_dict=feed_dict)
        if iteration % save_iterations == 0:
          print('Saving model to ', hp_save_dir)
          model_file = '{}/my_policy_net_pg.ckpt'.format(hp_save_dir)
          saver.save(sess, model_file)
          # Also save event files for TB.
          merge = tf.summary.merge_all()
          summary = sess.run(merge, feed_dict={episode_reward: avg_reward})
          train_writer.add_summary(summary, iteration)
      obs = env.reset()
      steps = []
      done = False
  else:  # Make a gif.
    from moviepy.editor import ImageSequenceClip
    model_file = '{}/my_policy_net_pg.ckpt'.format(outdir)
    with tf.Session() as sess:
      sess.run(tf.global_variables_initializer())
      saver.restore(sess, save_path=model_file)
      # Run model.
      obs = env.reset()
      done = False
      steps = []
      rewards = []
      while not done:
        s = env.render('rgb_array')
        steps.append(s)
        action_val = sess.run(action, feed_dict={X: obs.reshape(1, n_inputs)})
        obs, reward, done, info = env.step(action_val[0][0])
        rewards.append(reward)
      print('Final reward :', np.mean(rewards))
    clip = ImageSequenceClip(steps, fps=30)
    clip.write_gif('cartpole.gif', fps=30)
