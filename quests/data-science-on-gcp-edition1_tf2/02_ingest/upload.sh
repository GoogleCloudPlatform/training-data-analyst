#!/bin/bash
export BUCKET=${BUCKET:=cloud-training-demos-ml}
echo "Uploading to bucket $BUCKET..."
gcloud storage cp *.csv gs://$BUCKET/flights/raw
#gcloud storage objects update --recursive --add-acl-grant=entity=domain-google.com,role=READER gs://$BUCKET/flights/raw
