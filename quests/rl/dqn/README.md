# Hyperparameter Tuning for Deep Q Agents on GCP

Demonstrates how to use GCP Hyperparamter tuning for Deep Q Networks.

## To Run

From this directory, to run locally:

```
gcloud ai-platform local train --module-name=trainer.trainer --package-path=$PWD/trainer/
```

From this directory, to run on GCP's hyperparameter tuning service:

```
PROJECT=<my-awesome-project>
BUCKET=<my-awesome-bucket>
JOB_NAME=dqn_on_gcp_$(date -u +%y%m%d_%H%M%S)
REGION='us-central1'
IMAGE_URI=gcr.io/$PROJECT/dqn_on_gcp

gcloud builds submit --tag $IMAGE_URI .

gcloud ai-platform jobs submit training $JOB_NAME --staging-bucket=gs://$BUCKET  --region=$REGION    --master-image-uri=$IMAGE_URI --scale-tier=BASIC_GPU --job-dir=gs://$BUCKET/$JOB_NAME --config=hyperparam.yaml
```

## Resources
This code was inspired by the following resources:
* [An introduction to Deep Q-Learning: let’s play Doom](https://www.freecodecamp.org/news/an-introduction-to-deep-q-learning-lets-play-doom-54d02d8017d8/) by Thomas Simonini
* [Beat Atari with Deep Reinforcement Learning! (Part 1: DQN)](https://becominghuman.ai/lets-build-an-atari-ai-part-1-dqn-df57e8ff3b26) by Adrien Lucas Ecoffet
* [Deep reinforcement learning on GCP: using hyperparameter tuning and Cloud ML Engine to best OpenAI Gym games](https://cloud.google.com/blog/products/ai-machine-learning/deep-reinforcement-learning-on-gcp-using-hyperparameters-and-cloud-ml-engine-to-best-openai-gym-games) by Praneet Dutta, Chris Rawles, and Yujin Tang
* [Georgia Tech's Machine Learning Specialization](https://www.omscs.gatech.edu/specialization-machine-learning)