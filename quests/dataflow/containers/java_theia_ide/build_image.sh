#!/bin/bash

export IMAGE_URI=gcr.io/qwiklabs-resources/java-theia-ide-training-data-analyst

echo "Building and pushing using Cloud Build"
gcloud builds submit --timeout 15m --tag $IMAGE_URI
