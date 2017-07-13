#!/bin/bash

if [ "$#" -ne 2 ]; then
   echo "Usage:   ./run_oncloud.sh project-name  bucket-name"
   echo "Example: ./run_oncloud.sh cloud-training-demos  cloud-training-demos"
   exit
fi

PROJECT=$1
BUCKET=$2

gsutil -m rm -rf gs://$BUCKET/landsat/output

python ./dfndvi.py \
    --project=$PROJECT \
    --runner=DataflowRunner \
    --staging_location=gs://$BUCKET/landsat/staging \
    --temp_location=gs://$BUCKET/landsat/staging \
    --index_file=gs://cloud-training-demos/landsat/2015index.txt.gz \
    --max_num_workers=10 \
    --autoscaling_algorithm=THROUGHPUT_BASED \
    --output_file=gs://$BUCKET/landsat/output/scenes.txt \
    --output_dir=gs://$BUCKET/landsat/output \
    --job_name=monthly-landsat \
    --save_main_session \
    --setup_file=./setup.py
