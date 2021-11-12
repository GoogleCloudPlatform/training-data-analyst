#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./predict.sh bucket-name project-id"
    exit
fi

BUCKET=$1
PROJECT=$2

gsutil -m rm -rf gs://$BUCKET/flights/chapter10/output
bq rm -f flights.predictions

cd chapter10

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.flights.AddRealtimePrediction \
 -Dexec.args="--realtime --speedupFactor=60 --maxNumWorkers=10 --autoscalingAlgorithm=THROUGHPUT_BASED --bucket=$BUCKET --project=$PROJECT"

