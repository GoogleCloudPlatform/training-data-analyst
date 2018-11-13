#!/bin/bash

CLUSTERNAME=mykfp
ZONE=us-central1-b

gcloud config set compute/zone $ZONE
gcloud container clusters create $CLUSTERNAME \
  --zone $ZONE \
  --scopes cloud-platform \
  --enable-cloud-logging \
  --enable-cloud-monitoring \
  --machine-type n1-standard-2 \
  --num-nodes 4
kubectl create clusterrolebinding ml-pipeline-admin-binding --clusterrole=cluster-admin --user=$(gcloud config get-value account)
