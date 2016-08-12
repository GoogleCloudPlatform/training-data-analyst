#!/bin/bash

if [ "$#" -ne 3 ]; then
   echo "Usage:   ./run_oncloud.sh project-name  bucket-name  mainclassname"
   echo "Example: ./run_oncloud.sh cloud-training-demos  cloud-training-demos  StreamDemo[Consumer/Producer]"
   exit
fi

PROJECT=$1
BUCKET=$2
MAIN=com.google.cloud.training.dataanalyst.javahelp.$3

echo "project=$PROJECT  bucket=$BUCKET  main=$MAIN"

~/apache-maven-3.3.9/bin/mvn compile -e exec:java \
 -Dexec.mainClass=$MAIN \
      -Dexec.args="--project=$PROJECT \
      --stagingLocation=gs://$BUCKET/staging/ \
      --tempLocation=gs://$BUCKET/staging/ \
      --output=projects/$PROJECT/topics/streamdemo2 \
      --input=projects/$PROJECT/topics/streamdemo \
      --runner=DataflowPipelineRunner"
