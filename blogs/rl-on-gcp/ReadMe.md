# Reinforcement Learning on the Google Cloud Platform (GCP)

We present examples of running reinforcement learning (RL) algorithms on GCP
using Cloud ML Engine. Specifically, we provide implementations of [Vanilla Policy Gradient](https://papers.nips.cc/paper/1713-policy-gradient-methods-for-reinforcement-learning-with-function-approximation.pdf), [DQN](https://storage.googleapis.com/deepmind-media/dqn/DQNNaturePaper.pdf), [DDPG](https://arxiv.org/abs/1509.02971) and [TD3](https://arxiv.org/abs/1802.09477) with hyperparameter tuning.

We use this to train and tune their hyper-parameters in the 
[Cartpole](https://gym.openai.com/envs/CartPole-v0/),
[Breakout](https://gym.openai.com/envs/Breakout-v0/) and
[BipedalWalker](https://gym.openai.com/envs/BipedalWalker-v2) environments.

The directory is structured with Cartpole and Breakout in sub-folders. Each has their own
ReadMe with instructions, and sample code. BipedalWalker can be found [here](https://github.com/GoogleCloudPlatform/cloudml-samples)




