#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "Usage: ./build.sh  Ex0  [...]"
    exit
fi

PROJECT=$(gcloud config get-value project)
CBT_INSTANCE=datasme-cbt
#PACKAGE=com.google.cloud.bigtable.training
PACKAGE=com.google.cloud.bigtable.training.solutions
EXERCISE=$1
shift

mvn compile exec:java -Dexec.mainClass=${PACKAGE}.${EXERCISE} -Dbigtable.project=$PROJECT -Dbigtable.instance=$CBT_INSTANCE -Dbigtable.table=${EXERCISE}Table -Dexec.args="$@" -Dexec.cleanupDaemonThreads=false
