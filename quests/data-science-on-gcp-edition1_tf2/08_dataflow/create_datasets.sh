#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./create_datasets.sh  bucket-name max-num-workers"
    exit
fi

PROJECT=$DEVSHELL_PROJECT_ID
BUCKET=$1
MAX_NUM_WORKERS=$2

gsutil -m rm -rf gs://$BUCKET/flights/chapter8

cd chapter8

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.flights.CreateTrainingDataset \
 -Dexec.args="--project=$PROJECT --bucket=$BUCKET --fullDataset=true --maxNumWorkers=$MAX_NUM_WORKERS --autoscalingAlgorithm=THROUGHPUT_BASED"

# --workerMachineType=n1-highmem-8"
