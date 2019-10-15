#!/bin/bash

cd pipeline
rm -rf ../output

PROJECT_ID=$(gcloud config get-value project)

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.mlongcp.BabyweightMLService \
 -Dexec.args="$PROJECT_ID"
