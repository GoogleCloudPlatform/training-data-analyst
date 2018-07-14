#!/bin/bash

PROJECTID=$(gcloud config get-value project)

cd pipeline
bq mk babyweight
bq rm -rf babyweight.predictions

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.mlongcp.AddPrediction \
 -Dexec.args="--realtime --input=babies --output=babyweight.predictions --project=$PROJECTID"

