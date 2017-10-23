#!/bin/bash

cd pipeline
rm -rf ../output
mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.aslmlimmersion.BabyweightMLService
