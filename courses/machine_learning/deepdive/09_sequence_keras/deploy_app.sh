#!/bin/bash

cd application
#gcloud app create
gcloud app deploy --quiet --stop-previous-version app.yaml

PROJECT=$(gcloud config get-value project)

echo "Visit https://mlpoetry-dot-${PROJECT}.appspot.com"

