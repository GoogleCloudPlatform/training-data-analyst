#!/bin/bash

PROJECT=$(gcloud config get-value project)
echo ${PROJECT}

curl -X POST \
  -H "Authorization: Bearer "$(gcloud auth application-default print-access-token) \
  -H "Content-Type: application/json; charset=utf-8" \
  -d @request.json \
  https://us-documentai.googleapis.com/v1beta2/projects/${PROJECT}/locations/us/documents:process

