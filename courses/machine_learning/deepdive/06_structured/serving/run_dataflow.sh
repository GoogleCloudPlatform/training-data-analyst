#!/bin/bash

PROJECT_ID=$(gcloud config get-value project)

cd pipeline
bq mk babyweight
bq rm -f babyweight.predictions

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.mlongcp.AddPrediction \
 -Dexec.args="--realtime --input=babies --output=babyweight.predictions --project=$PROJECT_ID"
