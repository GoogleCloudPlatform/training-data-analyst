#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh


gcloud beta ai-platform jobs submit training $JOBID \
   --staging-bucket=gs://$BUCKET \
   --region=$REGION \
   --master-image-uri=$IMAGE_URI \
   --master-machine-type=n1-standard-4 \
   --scale-tier=CUSTOM \
  -- \
  --eval_data_path $EVAL_DATA_PATH \
  --output_dir $OUTPUT_DIR \
  --train_data_path $TRAIN_DATA_PATH \
  --batch_size 5 \
  --num_examples_to_train_on 100 \
  --num_evals 1 \
  --nbuckets 10 \
  --nnsize 32 8

