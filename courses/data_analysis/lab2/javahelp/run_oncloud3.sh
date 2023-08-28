#!/bin/bash

if [ "$#" -ne 4 ]; then
   echo "Usage:   ./run_oncloud.sh project-name  bucket-name  mainclass-basename"
   echo "Example: ./run_oncloud.sh cloud-training-demos  cloud-training-demos  JavaProjectsThatNeedHelp"
   exit
fi

PROJECT=$1
BUCKET=$2
MAIN=com.google.cloud.training.dataanalyst.javahelp.$3
REGION=$4

echo "project=$PROJECT  bucket=$BUCKET  main=$MAIN region=$REGION"

export PATH=/usr/lib/jvm/java-8-openjdk-amd64/bin/:$PATH
mvn compile -e exec:java \
 -Dexec.mainClass=$MAIN \
      -Dexec.args="--project=$PROJECT \
      --stagingLocation=gs://$BUCKET/staging/ \
      --tempLocation=gs://$BUCKET/staging/ \
      --outputPrefix=gs://$BUCKET/javahelp/output \
      --region=$REGION \
      --workerMachineType=e2-standard-2 \
      --runner=DataflowRunner"
