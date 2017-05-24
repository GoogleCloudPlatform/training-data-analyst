#!/bin/bash

mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.public_datasets.nexrad2.APPipeline \
 -Dexec.args="--numWorkers=5 --autoscalingAlgorithm=NONE --workerMachineType=n1-highmem-8 --radars=KYUX --years=2012 --months=7 --days=23"


# -Dexec.args="--maxNumWorkers=15 --autoscalingAlgorithm=THROUGHPUT_BASED --workerMachineType=n1-highmem-8 --radars=KYUX,KIWA,KFSX --years=2012,2013,2014 --months=6,7,8"




