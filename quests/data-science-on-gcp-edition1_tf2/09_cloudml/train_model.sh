#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage:        ./train_model.sh  destination-bucket-name func  num_examples"
    echo "   eg:        ./train_model.sh  cloud-training-demos-ml linear 100000"
    echo "func can be:  linear OR wide_deep"
    exit
fi

BUCKET=$1
PROJECT=$(gcloud config get-value project)
FUNC=$2
NUM_EXAMPLES=$3
REGION=us-central1

JOBID=flights_$(date +%Y%m%d_%H%M%S)
gsutil -m rm -rf gs://$BUCKET/flights/trained_model

gcloud ai-platform jobs submit training $JOBID \
   --staging-bucket=gs://$BUCKET  --region=$REGION \
   --module-name=trainer.task \
   --python-version=3.7 --runtime-version=2.1 \
   --package-path=${PWD}/flights/trainer \
   --master-machine-type=n1-standard-4 --scale-tier=CUSTOM \
   -- \
   --bucket=$BUCKET --num_examples=${NUM_EXAMPLES} --func=${FUNC}
