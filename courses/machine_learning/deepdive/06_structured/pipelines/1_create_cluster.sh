#!/bin/bash

CLUSTERNAME=mykfp3
ZONE=us-central1-a

gcloud config set compute/zone $ZONE
gcloud beta container clusters create $CLUSTERNAME \
  --cluster-version 1.11.2-gke.26 --enable-autoupgrade \
  --zone $ZONE \
  --scopes cloud-platform \
  --enable-cloud-logging \
  --enable-cloud-monitoring \
  --machine-type n1-standard-2 \
  --enable-autoscaling --max-nodes=10 --min-nodes=3 

# --num-nodes 4 
#  --preemptible \
#  --enable-autoprovisioning --max-cpu=40 --max-memory=1024 \

kubectl create clusterrolebinding ml-pipeline-admin-binding --clusterrole=cluster-admin --user=$(gcloud config get-value account)

kubectl create clusterrolebinding pipelinerunnerbinding \
  --clusterrole=cluster-admin \
  --serviceaccount=kubeflow:pipeline-runner
