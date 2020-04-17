# Simple RL on GCP example

Solves Cartpole using OpenAI's gym using vanilla policy gradients (PG) with TensorFlow. Below are steps:

1. Train model locally
2. Train on Google Cloud ML Engine
3. Train on Google Cloud ML Engine, performing hyperparameter tuning (uses Bayesian Optimization)

<img src="rl_model_code/cartpole.gif?raw=true" alt="drawing" width="400"/>

## Training

### Train model locally:

```
OUTPUT_DIR=rl_model
JOBNAME=rl_train_$(date -u +%y%m%d_%H%M%S)
REGION=us-central1
PACKAGE_PATH=$PWD/rl_model_code/trainer
export PYTHONPATH=${PYTHONPATH}:${PWD}/rl_model_code
rm $OUTPUT_DIR

gcloud ml-engine local train\
    --package-path=$PACKAGE_PATH\
    --module-name=trainer.task\
    --\
    --outdir=$OUTPUT_DIR
```

### On cloud:

```
JOBNAME=rl_job_$(date -u +%y%m%d_%H%M%S)
BUCKET=gs://YOUR-BUCKET-HERE
OUTPUT_DIR=gs://YOUR-BUCKET-HERE/rl/
REGION='us-central1'
PACKAGE_PATH=$PWD/rl_model_code/trainer
gsutil rm -r $OUTPUT_DIR
echo $OUTPUT_DIR
gcloud ml-engine jobs submit training $JOBNAME \
  --package-path=$PACKAGE_PATH \
  --module-name=trainer.task \
  --region=$REGION \
  --staging-bucket=$BUCKET\
  --scale-tier=BASIC \
  --runtime-version=1.10 \
  -- \
  --outdir=$OUTPUT_DIR\
  --n_games_per_update=5
```

### Train using HP tuning:

First create a hyperparam.yaml:


```
trainingInput:
  scaleTier: BASIC
  hyperparameters:
    maxTrials: 40
    maxParallelTrials: 5
    enableTrialEarlyStopping: False
    goal: MAXIMIZE
    hyperparameterMetricTag: reward
    params:
    - parameterName: n_games_per_update
      type: INTEGER
      minValue: 2
      maxValue: 20
      scaleType: UNIT_LINEAR_SCALE
    - parameterName: discount_rate
      type: DOUBLE
      minValue: 0.8
      maxValue: 0.99
      scaleType: UNIT_LOG_SCALE
    - parameterName: learning_rate
      type: DOUBLE
      minValue: 0.001
      maxValue: 0.1
      scaleType: UNIT_LOG_SCALE
    - parameterName: n_hidden
      type: DISCRETE
      discreteValues:
      - 4
      - 16
      - 32
```

Then submit a ML Engine HP job (note the `--config` argument).

```
JOBNAME=hp_rl_job_$(date -u +%y%m%d_%H%M%S)
BUCKET=gs://YOUR-BUCKET-HERE
OUTPUT_DIR=gs://YOUR-BUCKET-HERE/hp_results
REGION='us-central1'
PACKAGE_PATH=$PWD/rl_model_code/trainer
gsutil rm -r $OUTPUT_DIR
echo $OUTPUT_DIR
gcloud ml-engine jobs submit training $JOBNAME \
  --package-path=$PACKAGE_PATH \
  --module-name=trainer.task \
  --region=$REGION \
  --staging-bucket=$BUCKET\
  --runtime-version=1.10 \
  --config=hyperparam.yaml\
  -- \
  --outdir=$OUTPUT_DIR
```

## Evaluation

Make sure to use same number of hidden nodes, as used during training. Note the `eval` flag.

```
SAVED_MODEL=gs://YOUR-BUCKET-HERE/hp_results/BEST_TRIAL_ID
JOBNAME=rl_train_$(date -u +%y%m%d_%H%M%S)
REGION='us-central1'
PACKAGE_PATH=$PWD/rl_model_code/trainer
export PYTHONPATH=${PYTHONPATH}:${PWD}/rl_model_code
gcloud ml-engine local train\
    --package-path=$PACKAGE_PATH\
    --module-name=trainer.task\
    --\
    --outdir=$SAVED_MODEL\
    --n_hidden=16\
    --eval
```
