#!/bin/bash


PROJECT=$(gcloud config get-value project)
CBT_INSTANCE=datasme-cbt
EXERCISE=Ex0

PACKAGE=com.google.cloud.bigtable.training
shift

mvn compile exec:java -Dexec.mainClass=${PACKAGE}.${EXERCISE} -Dbigtable.project=$PROJECT -Dbigtable.instance=$CBT_INSTANCE -Dbigtable.table=TrainingTable -Dexec.args="$@" -Dexec.cleanupDaemonThreads=false
