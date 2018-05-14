#!/bin/bash

if [ "$#" -ne 5 ]; then
    echo "Usage: ./run_dv.sh  bucket   zone  yaml_file  reference_genome    bam_file"
    echo "   eg: ./run_dv.sh  cloud-training-demos-ml  us-central1-b  ./dv_rice.yaml  gs://rice-3k/reference/Os-Nipponbare-Reference-IRGSP-1.0/Os-Nipponbare-Reference-IRGSP-1.0.fa  gs://rice-3k/PRJEB6180/aligned-Os-Nipponbare-Reference-IRGSP-1.0/ERS467753.bam" 
    exit
fi

YAML=$3
PREFIX=$(basename $YAML | sed 's/.yaml//g')

set -euo pipefail
# Set common settings.
PROJECT_ID=$(gcloud config get-value project)
OUTPUT_BUCKET=gs://$1
STAGING_FOLDER_NAME=${PREFIX}_$(date +%s)
OUTPUT_FILE_NAME=${PREFIX}_output.vcf
# Model for calling whole genome sequencing data.
MODEL=gs://deepvariant/models/DeepVariant/0.6.0/DeepVariant-inception_v3-0.6.0+cl-191676894.data-wgs_standard
IMAGE_VERSION=0.6.1
DOCKER_IMAGE=gcr.io/deepvariant-docker/deepvariant:"${IMAGE_VERSION}"
DOCKER_IMAGE_GPU=gcr.io/deepvariant-docker/deepvariant_gpu:"${IMAGE_VERSION}"

# Run the pipeline.
gcloud alpha genomics pipelines run \
  --project "${PROJECT_ID}" \
  --pipeline-file ${YAML} \
  --logging "${OUTPUT_BUCKET}"/${STAGING_FOLDER_NAME}/runner_logs \
  --zones us-west1-b \
  --inputs `echo \
      PROJECT_ID="${PROJECT_ID}", \
      OUTPUT_BUCKET="${OUTPUT_BUCKET}", \
      MODEL="${MODEL}", \
      DOCKER_IMAGE="${DOCKER_IMAGE}", \
      DOCKER_IMAGE_GPU="${DOCKER_IMAGE_GPU}", \
      STAGING_FOLDER_NAME="${STAGING_FOLDER_NAME}"/staging, \
      INPUT_REF=$4, \
      INPUT_BAM=$5, \
      ZONES=$2, \
      OUTPUT_FILE_NAME="${OUTPUT_FILE_NAME}" \
      | tr -d '[:space:]'`
