# Hyperparameter Tuning for Deep Q Agents on GCP

Demonstrates how to use GCP Hyperparamter tuning for Deep Q Networks.

## To Run

From this directory, to run locally:

```
gcloud ml-engine local train --module-name=trainer.trainer --package-path=$PWD/trainer/
```

From this directory, to run on GCP's hyperparameter tuning service:

```
BUCKET=<my-awesome-bucket>
JOBNAME=<my-awesome-job-name>
REGION='us-central1'

gcloud ml-engine jobs submit training $JOBNAME --package-path=$PWD/trainer --module-name=trainer.trainer --region=$REGION --staging-bucket=gs://$BUCKET --scale-tier=BASIC --runtime-version=1.10 --job-dir=gs://$BUCKET/cartpole --config=hyperparam.yaml
```

## Resources
This code was inspired by the following resources:
* [An introduction to Deep Q-Learning: let’s play Doom](https://www.freecodecamp.org/news/an-introduction-to-deep-q-learning-lets-play-doom-54d02d8017d8/) by Thomas Simonini
* [Deep reinforcement learning on GCP: using hyperparameter tuning and Cloud ML Engine to best OpenAI Gym games](https://cloud.google.com/blog/products/ai-machine-learning/deep-reinforcement-learning-on-gcp-using-hyperparameters-and-cloud-ml-engine-to-best-openai-gym-games) by Praneet Dutta, Chris Rawles, and Yujin Tang
* [Georgia Tech's Machine Learning Specialization](https://www.omscs.gatech.edu/specialization-machine-learning)


## Todos
* Add more detail to this readme
* Move to keras and TF2,0
* Add an eval function to import a model
* Reduce the amount of time to finish training (currently 20 minutes)