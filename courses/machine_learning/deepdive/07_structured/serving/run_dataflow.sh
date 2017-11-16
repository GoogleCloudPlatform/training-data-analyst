#!/bin/bash

cd pipeline
bq mk babyweight
bq rm -rf babyweight.predictions

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.aslmlimmersion.AddPrediction \
 -Dexec.args="--realtime --input=babies --output=babyweight.predictions --project=$1"

