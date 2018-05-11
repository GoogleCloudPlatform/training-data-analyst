#!/bin/bash


set -euo pipefail
# Set common settings.
PROJECT_ID=$(gcloud config get-value project)
OUTPUT_BUCKET=gs://OUTPUT_BUCKET
STAGING_FOLDER_NAME=[a unique alphanumeric name for each run]
OUTPUT_FILE_NAME=output.vcf
# Model for calling whole genome sequencing data.
MODEL=gs://deepvariant/models/DeepVariant/0.6.0/DeepVariant-inception_v3-0.6.0+cl-191676894.data-wgs_standard
# Model for calling exome sequencing data.
# MODEL=gs://deepvariant/models/DeepVariant/0.6.0/DeepVariant-inception_v3-0.6.0+cl-191676894.data-wes_standard
IMAGE_VERSION=0.6.1
DOCKER_IMAGE=gcr.io/deepvariant-docker/deepvariant:"${IMAGE_VERSION}"
DOCKER_IMAGE_GPU=gcr.io/deepvariant-docker/deepvariant_gpu:"${IMAGE_VERSION}"

# Run the pipeline.


gcloud alpha genomics pipelines run \
  --project "${PROJECT_ID}" \
  --pipeline-file deepvariant_pipeline.yaml \
  --logging "${OUTPUT_BUCKET}"/runner_logs \
  --zones us-west1-b \
  --inputs `echo \
      PROJECT_ID="${PROJECT_ID}", \
      OUTPUT_BUCKET="${OUTPUT_BUCKET}", \
      MODEL="${MODEL}", \
      DOCKER_IMAGE="${DOCKER_IMAGE}", \
      DOCKER_IMAGE_GPU="${DOCKER_IMAGE_GPU}", \
      STAGING_FOLDER_NAME="${STAGING_FOLDER_NAME}", \
      OUTPUT_FILE_NAME="${OUTPUT_FILE_NAME}" \
      | tr -d '[:space:]'`
