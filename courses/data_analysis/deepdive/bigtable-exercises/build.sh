#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./build.sh  Ex0"
    exit
fi

PROJECT=$(gcloud config get-value project)
CBT_INSTANCE=datasme-cbt
EXERCISE=$1

mvn compile exec:java -Dexec.mainClass=com.google.cloud.bigtable.training.${EXERCISE} -Dbigtable.project=$PROJECT -Dbigtable.instance=$CBT_INSTANCE -Dbigtable.table=${EXERCISE}Table
