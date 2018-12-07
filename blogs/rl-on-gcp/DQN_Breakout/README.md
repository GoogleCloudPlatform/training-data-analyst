# DEEP Q-LEARNING ON ATARI BREAKOUT

The given module provides examples for training, evaluating and Hyper-parameter tuning of the popular [DQN algorithm](https://deepmind.com/research/dqn/) on the OpenAI Gym environment ["Atari Breakout"](https://gym.openai.com/envs/Breakout-v0/).


## Learnt DQN agent
![Episode 500](img/breakout_4.0.gif?raw=true)  
The agent couldnt play the game very well initially  

![Episode 2000](img/breakout_18.0.gif?raw=true)   
After being trained for 2000 episodes, the agent is able to start to breakdown the blocks 

![Episode 5000](img/breakout_36.0.gif?raw=true)   
As training progresses, the agents begins obtaining good results in the game. 

## Installing Packages

Install all of the dependencies in the requirements.txt :-

```
pip install -r requirements.txt
```


## Training

Train model locally:

```
gcloud ml-engine local train \
   --module-name=trainer.trainer \
   --package-path=${PWD}/rl_on_gcp/trainer \
   --\
   --steps=500000\
   --start_train=5000\
   --buffer_size=10000\
   --save_model=True\
   --model_dir='my_model'
```

Train model on cloud:

```
# On cloud.
JOBNAME=rl_breakout_$(date -u +%y%m%d_%H%M%S)
REGION= REGION
Example('us-central1')
BUCKET=SAMPLE_BUCKET_NAME
MODEL=SAMPLE_MODEL_PATH 

gcloud ml-engine jobs submit training $JOBNAME \
        --package-path=$PWD/rl_on_gcp/trainer \
        --module-name=trainer.trainer \
        --region=$REGION \
        --staging-bucket=gs://$BUCKET \
        --scale-tier=BASIC\
        --runtime-version=1.10 \
        --\
        --steps=5000000\
        --start_train=5000\
        --buffer_size=500000\
        --save_model=True\
        --model_dir='gs://BUCKET/MODEL'
```

Train using HP tuning:

For Hyper-parameter(HP) tuning, it is required to define the list of parameters to be tuned and then running a HP job which tests combinations of these combinations optimizing for reward. A sample .yaml file is provided for reference.

```
# Creating a .yaml File
trainingInput:
  scaleTier: BASIC_GPU
  hyperparameters:
    maxTrials: 40
    maxParallelTrials: 5
    enableTrialEarlyStopping: False
    goal: MAXIMIZE    
    hyperparameterMetricTag: reward
    params:
    - parameterName: update_target
      type: INTEGER
      minValue: 500
      maxValue: 5000
      scaleType: UNIT_LOG_SCALE
    - parameterName: init_eta
      type: DOUBLE
      minValue: 0.8
      maxValue: 0.95
      scaleType: UNIT_LOG_SCALE
    - parameterName: learning_rate
      type: DOUBLE
      minValue: 0.00001
      maxValue: 0.001
      scaleType: UNIT_LOG_SCALE
    - parameterName: batch_size
      type: DISCRETE
      discreteValues:
      - 4
      - 16
      - 32
      - 64
      - 128
      - 256
      - 512
```

```
# HP job on cloud.
JOBNAME=rl_breakout_hp_$(date -u +%y%m%d_%H%M%S)
BUCKET=SAMPLE_BUCKET_NAME
MODEL=SAMPLE_MODEL_PATH 

gcloud ml-engine jobs submit training $JOBNAME \
        --package-path=$PWD/rl_on_gcp/trainer \
        --module-name=trainer.trainer \
        --region=$REGION \
        --staging-bucket=gs://$BUCKET \
        --config=hyperparam.yaml \
        --runtime-version=1.10 \
        --\
        --steps=100000\
        --start_train=5000\
        --buffer_size=500000\
        --model_dir='gs://BUCKET/MODEL/'
```

## Evaluation

Make sure to use same model architecture and inputs, as used during training. Note the `eval` mode.

```
SAVED_MODEL= SAVED_MODEL_PATH

PACKAGE_PATH=$PWD/rl_model_code/trainer
export PYTHONPATH=${PYTHONPATH}:${PWD}/rl_model_code

gcloud ml-engine local train\
    --package-path=$PACKAGE_PATH\
    --module-name=trainer.task\
    --\
    --mode="eval"
    --load_model=$SAVED_MODEL\
```

