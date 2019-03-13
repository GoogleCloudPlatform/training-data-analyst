#!/bin/bash

set -ex

if [ "$#" -ne 2 ]; then
    echo "Usage: ./train.sh  hyperparam_jobname  bucket-name"
    exit
fi

HYPERJOB=$1
BUCKET=$2
TFVERSION=1.8
REGION=us-central1

echo "Extracting information for job $HYPERJOB"

# get information from the best hyperparameter job
RMSE=$(gcloud ml-engine jobs describe $HYPERJOB --format 'value(trainingOutput.trials.finalMetric.objectiveValue.slice(0))')
NNSIZE=$(gcloud ml-engine jobs describe $HYPERJOB --format 'value(trainingOutput.trials.hyperparameters.nnsize.slice(0))')
BATCHSIZE=$(gcloud ml-engine jobs describe $HYPERJOB --format 'value(trainingOutput.trials.hyperparameters.batch_size.slice(0))')
NEMBEDS=$(gcloud ml-engine jobs describe $HYPERJOB --format 'value(trainingOutput.trials.hyperparameters.nembeds.slice(0))')
TRIALID=$(gcloud ml-engine jobs describe $HYPERJOB --format 'value(trainingOutput.trials.trialId.slice(0))')

echo "Continuing to train model in $TRIALID with nnsize=$NNSIZE batch_size=$BATCHSIZE nembeds=$NEMBEDS"

# directory containing trainer package in Docker image
# see Dockerfile
CODEDIR=/babyweight/src/training-data-analyst/courses/machine_learning/deepdive/06_structured

OUTDIR=gs://${BUCKET}/babyweight/hyperparam/$TRIALID
export PYTHONPATH=${CODEDIR}/babyweight:${PYTHONPATH}

python -m trainer.task \
  --job-dir=$OUTDIR \
  --bucket=${BUCKET} \
  --output_dir=${OUTDIR} \
  --eval_steps=10 \
  --nnsize=$NNSIZE \
  --batch_size=$BATCHSIZE \
  --nembeds=$NEMBEDS \
  --train_examples=200000


# note --stream-logs above so that we wait for job to finish
# write output file for next step in pipeline
echo $OUTDIR > /output.txt

# for tensorboard
echo {\"type\":\"tensorboard\"\,\"source\":\"$OUTDIR\"} > /mlpipeline-ui-metadata.json

