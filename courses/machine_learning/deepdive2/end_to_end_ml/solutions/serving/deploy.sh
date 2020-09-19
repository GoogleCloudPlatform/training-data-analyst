#!/bin/bash

cd application
pip install -r requirements.txt -t lib
gcloud app create --region us-east1
gcloud app deploy

PROJECT=$(gcloud config get-value project)
echo "Visit https://PROJECT-ID.appspot.com/  e.g. https://${PROJECT}.appspot.com"
