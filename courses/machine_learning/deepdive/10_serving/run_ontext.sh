#!/bin/bash

cd pipeline
rm -rf ../output
mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.aslmlimmersion.AddPrediction \
 -Dexec.args="--input=../*.csv.gz --output=../output/ --project=$1"


