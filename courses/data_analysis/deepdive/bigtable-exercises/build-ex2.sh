#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "Usage: ./build.sh gs://YOUR-STAGING-BUCKET"
    exit
fi

PROJECT=$(gcloud config get-value project)
CBT_INSTANCE=datasme-cbt
EXERCISE=Ex2
STAGING=$1

PACKAGE=com.google.cloud.bigtable.training
shift

mvn compile exec:java -Dexec.mainClass=${PACKAGE}.${EXERCISE} -Dexec.args="--project=${PROJECT} --bigtableProjectId=${PROJECT}   --bigtableInstanceId=${CBT_INSTANCE} --bigtableTableId=TrainingTable --runner=BlockingDataflowPipelineRunner --stagingLocation=${STAGING} --inputFile=gs://cloud-bigtable-training/actions_subset.csv"




