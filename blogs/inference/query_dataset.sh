#!/bin/bash


if [ "$#" -lt 2 ]; then
   echo "Usage:   ./query_dataset.sh datasetname query_filename.json "
   exit
fi

DATASET=$1
FILE=$2

export GOOGLE_APPLICATION_CREDENTIALS=${PWD}/.access_key.json
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) | grep projectNumber | sed "s/'/ /g" | awk '{print $2}')
ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
echo $PROJECT_NUMBER $ACCESS_TOKEN

curl -s -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://infer.googleapis.com/v1/projects/${PROJECT_NUMBER}/datasets/${DATASET}:query \
  -d @${FILE}
