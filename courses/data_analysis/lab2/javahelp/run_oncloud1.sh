#!/bin/bash

if [ "$#" -ne 3 ]; then
   echo "Usage:   ./run_oncloud.sh project-name  bucket-name  mainclass-basename"
   echo "Example: ./run_oncloud.sh cloud-training-demos  cloud-training-demos  JavaProjectsThatNeedHelp"
   exit
fi

PROJECT=$1
BUCKET=$2
MAIN=com.google.cloud.training.dataanalyst.javahelp.$3

echo "project=$PROJECT  bucket=$BUCKET  main=$MAIN"

export PATH=/usr/lib/jvm/java-8-openjdk-amd64/bin/:$PATH
mvn compile -e exec:java \
 -Dexec.mainClass=$MAIN \
      -Dexec.args="--project=$PROJECT \
      --stagingLocation=gs://$BUCKET/staging/ \
      --tempLocation=gs://$BUCKET/staging/ \
      --runner=DataflowRunner"
