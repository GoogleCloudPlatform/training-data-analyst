#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./mvn_exec.sh  bucket-name max-num-workers"
    exit
fi

PROJECT=$(gcloud config get-value project)
BUCKET=$1
MAX_NUM_WORKERS=$2

cd bq_in_df

~/apache-maven*/bin/mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.dataflowsql.UpsetsByDay \
 -Dexec.args="--project=$PROJECT --bucket=$BUCKET --autoscalingAlgorithm=THROUGHPUT_BASED"

