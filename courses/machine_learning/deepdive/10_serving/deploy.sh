#!/bin/bash

cd application
pip install -r requirements.txt -t lib
gcloud app create
gcloud app deploy

echo "Visit https://PROJECT-ID.appspot.com/  e.g. https://asl-ml-immersion.appspot.com"
