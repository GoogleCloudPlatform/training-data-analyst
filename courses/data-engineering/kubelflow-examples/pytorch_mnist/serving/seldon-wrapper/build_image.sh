#!/bin/bash
#
# A simple script to build the Docker images.
# Adapted to generate Dockerfile for Seldon
# https://github.com/SeldonIO/seldon-core/blob/master/docs/wrappers/python-docker.md
#
# This is intended to be invoked as a step in Argo to build the docker image.
# build_image.sh ${DOCKERFILE} ${IMAGE} ${TAG}
set -ex

DOCKERFILE=$1
IMAGE=$2
TAG=$3
CONTEXT_DIR=$(dirname "$DOCKERFILE")
PROJECT="${GCP_PROJECT}"

# Wait for the Docker daemon to be available.
until docker ps
do sleep 3
done

gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}

cd $CONTEXT_DIR
echo "Generate Seldon Dockerfile and artifacts"
docker run -v ${CONTEXT_DIR}:/my_model seldonio/core-python-wrapper:0.7 /my_model mnistddpserving ${TAG} ${IMAGE} --grpc --force

echo "GCP Project: "$PROJECT
cd build
echo "Building image using gcloud build"
gcloud builds submit --tag=${IMAGE}:${TAG} --project=${PROJECT} .
echo "Finished building image"