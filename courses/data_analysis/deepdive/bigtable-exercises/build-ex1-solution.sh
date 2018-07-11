#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "Usage: ./build.sh <use buffered mutator true or false>"
    exit
fi

PROJECT=$(gcloud config get-value project)
CBT_INSTANCE=datasme-cbt
USEBM=$1
EXERCISE=Ex1Solution
PACKAGE=com.google.cloud.bigtable.training.solutions
shift

mvn compile exec:java -Dexec.mainClass=${PACKAGE}.${EXERCISE} -Dbigtable.project=$PROJECT -Dbigtable.instance=$CBT_INSTANCE -Dbigtable.table=TrainingTable -Dbigtable.useBufferedMutator=${USEBM} -Dexec.args="$@" -Dexec.cleanupDaemonThreads=false
