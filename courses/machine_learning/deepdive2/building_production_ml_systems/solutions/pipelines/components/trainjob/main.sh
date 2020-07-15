#!/bin/bash


BUCKET="$1"

BATCH_SIZE=5
NUM_EXAMPLES_TO_TRAIN_ON=100
NUM_EVALS=1
NBUCKETS=10
NNSIZE="32 8"
MACHINE_TYPE=n1-standard-4
SCALE_TIER=CUSTOM

REGION=us-west1

GCS_PROJECT_PATH=gs://$BUCKET/taxifare
DATA_PATH=$GCS_PROJECT_PATH/data
OUTPUT_DIR=$GCS_PROJECT_PATH/model
TRAIN_DATA_PATH=$DATA_PATH/taxi-train*
EVAL_DATA_PATH=$DATA_PATH/taxi-valid*

IMAGE_NAME=taxifare_training_container
PROJECT_ID=$(gcloud config list project --format "value(core.project)")
IMAGE_URI=gcr.io/$PROJECT_ID/$IMAGE_NAME

JOBID=taxifare_$(date +%Y%m%d_%H%M%S)

gcloud ai-platform jobs submit training $JOBID \
   --stream-logs \
   --staging-bucket=gs://$BUCKET \
   --region=$REGION \
   --master-image-uri=$IMAGE_URI \
   --master-machine-type=$MACHINE_TYPE \
   --scale-tier=$SCALE_TIER \
  -- \
  --eval_data_path $EVAL_DATA_PATH \
  --output_dir $OUTPUT_DIR \
  --train_data_path $TRAIN_DATA_PATH \
  --batch_size $BATCH_SIZE \
  --num_examples_to_train_on $NUM_EXAMPLES_TO_TRAIN_ON \
  --num_evals $NUM_EVALS \
  --nbuckets $NBUCKETS \
  --nnsize $NNSIZE 

