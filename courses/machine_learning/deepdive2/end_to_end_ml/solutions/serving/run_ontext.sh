#!/bin/bash

PROJECTID=$(gcloud config get-value project)

cd pipeline
rm -rf ../output
mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.mlongcp.AddPrediction \
 -Dexec.args="--input=../*.csv.gz --output=../output/ --project=$PROJECTID"


