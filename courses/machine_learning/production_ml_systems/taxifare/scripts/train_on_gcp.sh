#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh


gcloud beta ai-platform jobs submit training $JOBID \
   --staging-bucket=gs://$BUCKET  \
   --region=$REGION \
   --master-image-uri=$IMAGE_URI \
   --master-machine-type=n1-standard-4 \
   --scale-tier=CUSTOM \
  -- \
  --test=uuu
