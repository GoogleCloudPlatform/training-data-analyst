#!/bin/bash


BUCKET=cloud-training-demos
PROJECT=cloud-training-demos
gsutil -m rm -rf gs://$BUCKET/landsat/output

./dfndvi.py \
    --project=$PROJECT \
    --runner=DataflowPipelineRunner \
    --staging_location=gs://$BUCKET/landsat/staging \
    --temp_location=gs://$BUCKET/landsat/staging \
    --input_index=gs://gcp-public-data-landsat/index.csv.gz \
    --maxNworkers=100 \
    --output_file=gs://$BUCKET/landsat/output/scenes.txt \
    --output_dir=gs://$BUCKET/landsat/output \
    --job_name=monthly-landsat \
    --save_main_session \
    --setup_file=./setup.py
