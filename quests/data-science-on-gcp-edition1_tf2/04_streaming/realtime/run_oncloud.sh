#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./run_on_cloud.sh  bucket-name"
    exit
fi

PROJECT=$(gcloud config get-value project)
BUCKET=$1

cd chapter4

bq rm flights.streaming_delays   # delete existing table

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.flights.AverageDelayPipeline \
      -Dexec.args="--project=$PROJECT \
      --stagingLocation=gs://$BUCKET/staging/ \
      --gcpTempLocation=gs://$BUCKET/staging/tmp \
      --averagingInterval=60 \
      --speedupFactor=30 \
      --runner=DataflowRunner"

cd ..
