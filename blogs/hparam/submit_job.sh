#!/bin/bash
BUCKET=cloud-training-demos-ml
JOBNAME=hparam_$(date -u +%y%m%d_%H%M%S)
REGION=us-central1
gcloud ml-engine jobs submit training $JOBNAME \
  --region=$REGION \
  --module-name=trainer.flow \
  --package-path=$(pwd)/trainer \
  --job-dir=gs://$BUCKET/hparam/ \
  --config=hyperparam.yaml \
  -- \
  --flow=5
