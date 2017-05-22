#!/bin/bash

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.public_datasets.nexrad2.APPipeline \
 -Dexec.args="--numWorkers=15 --autoscalingAlgorithm=NONE --workerMachineType=n1-highmem-8"
