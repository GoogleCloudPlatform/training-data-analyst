#!/bin/bash

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: ./train.sh  bucket-name"
    exit
fi

BUCKET=$1
TFVERSION=1.8
REGION=us-central1

# directory containing trainer package in Docker image
# see Dockerfile
CODEDIR=/babyweight/src/training-data-analyst/courses/machine_learning/deepdive/06_structured

OUTDIR=gs://${BUCKET}/babyweight/hyperparam
JOBNAME=babyweight_$(date -u +%y%m%d_%H%M%S)
echo $OUTDIR $REGION $JOBNAME
gsutil -m rm -rf $OUTDIR
gcloud ml-engine jobs submit training $JOBNAME \
  --region=$REGION \
  --module-name=trainer.task \
  --package-path=${CODEDIR}/babyweight/trainer \
  --job-dir=$OUTDIR \
  --staging-bucket=gs://$BUCKET \
  --scale-tier=STANDARD_1 \
  --config=hyperparam.yaml \
  --runtime-version=$TFVERSION \
  --stream-logs \
  -- \
  --bucket=${BUCKET} \
  --output_dir=${OUTDIR} \
  --eval_steps=10 \
  --train_examples=20000


# note --stream-logs above so that we wait for job to finish
# write output file for next step in pipeline
echo $JOBNAME > /output.txt
