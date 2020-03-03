#!/bin/bash
#
# A simple script to build the Docker images.
# This is intended to be invoked as a step in Argo to build the docker image.
#
# build_image.sh ${DOCKERFILE} ${IMAGE} ${TAG}
set -ex

DOCKERFILE=$1
IMAGE=$2
TAG=$3
CONTEXT_DIR=$(dirname "$DOCKERFILE")
CONTEXT_NAME=$(basename "$DOCKERFILE")
PROJECT="${GCP_PROJECT}"

gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
gcloud auth configure-docker

cd $CONTEXT_DIR

echo "GCP Project: "$PROJECT

# Build image
echo "Building image: "$IMAGE
docker build "${CONTEXT_DIR}" -f ${CONTEXT_NAME} -t "${IMAGE}:${TAG}"
echo "Finished building image: "$IMAGE

# Push image
echo "Pushing image: "$IMAGE
docker push "${IMAGE}:${TAG}"
echo "Finished pushing image: "$IMAGE