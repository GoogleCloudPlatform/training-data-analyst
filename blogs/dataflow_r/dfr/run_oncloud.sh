#!/bin/bash

if [ "$#" -ne 2 ]; then
   echo "Usage:   ./run_oncloud.sh project-name  bucket-name"
   echo "Example: ./run_oncloud.sh cloud-training-demos  cloud-training-demos"
   exit
fi

PROJECT=$1
BUCKET=$2
MAIN=com.google.cloud.training.dataanalyst.dfr.CallingRFromJava

echo "project=$PROJECT  bucket=$BUCKET  main=$MAIN"

export PATH=/usr/lib/jvm/java-8-openjdk-amd64/bin/:$PATH
mvn compile -e exec:java \
 -Dexec.mainClass=$MAIN \
      -Dexec.args="--project=$PROJECT \
      --input=gs://cloud-training-demos/dataflow_r/numbers.csv.gz \
      --outputPrefix=gs://$BUCKET/dataflow_r/output \
      --stagingLocation=gs://$BUCKET/dataflow_r/staging/ \
      --tempLocation=gs://$BUCKET/dataflow_r/staging/ \
      --runner=BlockingDataflowPipelineRunner"
