#!/bin/bash

cd application
pip install -r requirements.txt -t lib
gcloud app create --region # TODO: Add region you want to create app in
gcloud app deploy

PROJECT=$(gcloud config get-value project)
echo "Visit https://PROJECT-ID.appspot.com/  e.g. https://${PROJECT}.appspot.com"
