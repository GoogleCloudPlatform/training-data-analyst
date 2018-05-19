#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: ./run_dv.sh  zone  yaml_file  reference_genome    bam_file"
    echo "   eg: ./run_dv.sh  us-central1-b  ./dv_rice.yaml  gs://rice-3k/reference/Os-Nipponbare-Reference-IRGSP-1.0/Os-Nipponbare-Reference-IRGSP-1.0.fa  gs://rice-3k/PRJEB6180/aligned-Os-Nipponbare-Reference-IRGSP-1.0/ERS467753.bam" 
    exit
fi

set -euo pipefail

# Set common settings.
ZONE=$1
YAML=$2
PREFIX=$(basename $YAML | sed 's/.yaml//g')   # e.g. dv_rice
INPUT_REF=$3
INPUT_BAM=$4
PROJECT_ID=$(gcloud config get-value project)
STAGING_FOLDER_NAME=staging
OUTPUT_FILE_NAME=output.vcf

# Make a unique output bucket
OUTPUT_BUCKET=gs://${PROJECT_ID}-${PREFIX}-$(date +%s)  # hopefully unique
REGION=$(echo $ZONE | sed 's/..$//')
gsutil mb -c regional -l $REGION $OUTPUT_BUCKET

#echo "INPUT_REF=$INPUT_REF"
#echo "INPUT_BAM=$INPUT_BAM"
#echo "ZONE=$ZONE"
#echo "REGION=$REGION"
echo "Output VCF will be at $OUTPUT_BUCKET/$OUTPUT_FILE_NAME"

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
  --zones $ZONE \
  --inputs `echo \
      PROJECT_ID="${PROJECT_ID}", \
      OUTPUT_BUCKET="${OUTPUT_BUCKET}", \
      MODEL="${MODEL}", \
      DOCKER_IMAGE="${DOCKER_IMAGE}", \
      DOCKER_IMAGE_GPU="${DOCKER_IMAGE_GPU}", \
      STAGING_FOLDER_NAME="${STAGING_FOLDER_NAME}"/staging, \
      INPUT_REF=$INPUT_REF, \
      INPUT_BAM=$INPUT_BAM, \
      ZONES=$ZONE, \
      OUTPUT_FILE_NAME="${OUTPUT_FILE_NAME}" \
      | tr -d '[:space:]'`
