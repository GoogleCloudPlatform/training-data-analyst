#!/bin/bash

export IMAGE_URI=gcr.io/qwiklabs-resources/theia-java-dataflow

echo "Building $IMAGE_URI"
docker build . -t $IMAGE_URI --no-cache

echo "Pushing $IMAGE_URI"
docker push $IMAGE_URI