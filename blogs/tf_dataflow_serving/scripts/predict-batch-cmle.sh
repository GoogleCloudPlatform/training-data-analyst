#!/usr/bin/env bash

#[START cmle_batch_prediction]
BUCKET='<BUCKET>'
DATA_FORMAT="TEXT"
INPUT_PATHS=gs://${BUCKET}/data/babyweight/experiments/outputs/data-prep-*
OUTPUT_PATH=gs://${BUCKET}/data/babyweight/experiments/outputs/cmle-estimates
MODEL_NAME='babyweight_estimator'
VERSION_NAME='v1'
REGION='<REGION>'
now=$(date +"%Y%m%d_%H%M%S")
JOB_NAME="batch_predict_$MODEL_NAME$now"
MAX_WORKER_COUNT="20"

gcloud ml-engine jobs submit prediction $JOB_NAME \
    --model=$MODEL_NAME \
    --input-paths=$INPUT_PATHS \
    --output-path=$OUTPUT_PATH \
    --region=$REGION \
    --data-format=$DATA_FORMAT \
    --max-worker-count=$MAX_WORKER_COUNT
#[END cmle_batch_prediction]
