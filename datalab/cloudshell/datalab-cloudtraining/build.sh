#!/bin/bash
IMAGE=gcr.io/cloud-training-demos/datalab-cloudtraining
docker build -t $IMAGE ./ && gcloud docker -- push $IMAGE
