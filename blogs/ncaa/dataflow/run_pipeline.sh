#!/bin/bash
# open cloud shell

# change below to your GCP Project id:
PROJECT='your-project-id'
REGION='us-central1'

sudo apt-get upgrade
sudo apt-get install python-pip

# install Apache Beam
python -m pip install --user apache-beam[gcp]
pip install -U pip

# set project defaults
gcloud components update
gcloud config set project $PROJECT
gcloud config set compute/region $REGION

# copy in pipeline code
gsutil cp gs://cloud-training-demos/ncaa/next-bootcamp/pipeline/play_by_play.py play_by_play.py

# inspect the code in the editor

python play_by_play.py --project_id $PROJECT --temp_location gs://$PROJECT/tmp --region $REGION --staging gs://${PROJECT}/tmp/staging

# navigate to Dataflow to monitor your job
# https://console.cloud.google.com/dataflow

# while you wait for the job to complete,
# copy this existing output table