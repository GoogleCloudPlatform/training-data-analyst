#!/bin/bash

if [ "$#" -ne 3 ]; then
   echo "Usage:   ./run_oncloud.sh project-name  bucket-name  python-file"
   echo "Example: ./run_oncloud.sh cloud-training-demos  cloud-training-demos  grep.py"
   exit
fi

PROJECT=$1
BUCKET=$2
MAIN=$3

echo "project=$PROJECT  bucket=$BUCKET  main=$MAIN"

python $3 \
      --project=$PROJECT \
      --job_name=myjob \
      --staging_location=gs://$BUCKET/staging/ \
      --temp_location=gs://$BUCKET/staging/ \
      --runner=BlockingDataflowPipelineRunner
