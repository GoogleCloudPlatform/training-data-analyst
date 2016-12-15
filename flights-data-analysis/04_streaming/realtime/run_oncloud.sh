#!/bin/bash

PROJECT=cloud-training-demos
BUCKET=cloud-training-demos-ml

cd chapter4
mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.flights.AverageDelayPipeline \
      -Dexec.args="--project=$PROJECT \
      --stagingLocation=gs://$BUCKET/staging/ \
      --averagingInterval=60 \
      --speedupFactor=30 \
      --runner=DataflowPipelineRunner"

cd ..
