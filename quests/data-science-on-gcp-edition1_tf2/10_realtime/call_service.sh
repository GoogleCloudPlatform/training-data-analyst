#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./call_service.sh bucket-name project-id"
    exit
fi

BUCKET=$1
PROJECT=$2


cd chapter10

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.flights.FlightsMLService \
 -Dexec.args="--realtime --speedupFactor=60 --maxNumWorkers=10 --autoscalingAlgorithm=THROUGHPUT_BASED --bucket=$BUCKET --project=$PROJECT"

