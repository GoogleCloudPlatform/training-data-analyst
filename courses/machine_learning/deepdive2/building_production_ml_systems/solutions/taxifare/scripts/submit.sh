#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh


BATCH_SIZE=5
NUM_EXAMPLES_TO_TRAIN_ON=100
NUM_EVALS=1
NBUCKETS=10
NNSIZE="32 8"
MACHINE_TYPE=n1-standard-4
SCALE_TIER=CUSTOM



# gcloud ai-platform jobs submit training $JOBID \
gcloud beta ai-platform jobs submit training $JOBID \
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

