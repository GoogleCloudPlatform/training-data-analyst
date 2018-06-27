#!/bin/bash
PROJECT=$(gcloud config get-value project)
SVC_ACCOUNT=$(curl -H "Authorization: Bearer $(gcloud auth print-access-token)"  \
    https://ml.googleapis.com/v1/projects/${PROJECT}:getConfig \
              | grep tpuServiceAccount | tr '"' ' ' | awk '{print $3}' )
echo "Enabling TPU service account $SVC_ACCOUNT to act as Cloud ML Service Agent"
gcloud projects add-iam-policy-binding $PROJECT \
    --member serviceAccount:$SVC_ACCOUNT --role roles/ml.serviceAgent
echo "Done"

