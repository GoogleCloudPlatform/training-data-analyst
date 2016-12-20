#!/bin/bash


BUCKET=cloud-training-demos
PROJECT=cloud-training-demos
gsutil -m rm -rf gs://$BUCKET/landsat/output

./dfndvi.py \
    --project=$PROJECT \
    --runner=DataflowPipelineRunner \
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
