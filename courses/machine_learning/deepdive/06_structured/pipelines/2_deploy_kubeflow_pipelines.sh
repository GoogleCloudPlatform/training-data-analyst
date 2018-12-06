#!/bin/bash
PIPELINE_VERSION=0.1.3
kubectl create -f https://storage.googleapis.com/ml-pipeline/release/$PIPELINE_VERSION/bootstrapper.yaml

kubectl get job
echo "Waiting until number of successful runs is 1 ..."

while [ $(kubectl get job | tail -1 | awk '{print $3}') -lt 1 ]
do 
echo "waiting"
sleep 1
done

kubectl get job


# This is an alternate method
# jobname=$(kubectl get job | tail -1 | awk '{print $1}')
# kubectl wait --for=condition=complete --timeout=5m $jobname
