#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS=${PWD}/.access_key.json
PROJECT_ID=$(gcloud projects describe $(gcloud config get-value project) | grep projectNumber | sed "s/'/ /g" | awk '{print $2}')
ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
curl -s -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://infer.googleapis.com/v1/projects/${PROJECT_ID}/datasets 
