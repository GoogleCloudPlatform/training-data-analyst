#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./deploy.sh  modelname  modelversion"
    exit
fi

# the appengine app gets model name and version from the environment
export MODEL_NAME=$1
export MODEL_VERSION=$2

cd /babyweight/src/training-data-analyst/courses/machine_learning/deepdive/06_structured/serving/application

pip install -r requirements.txt -t lib
gcloud app create
gcloud app deploy

# output
PROJECT=$(gcloud config get-value project)
echo "https://${PROJECT}.appspot.com" > /appurl.txt
