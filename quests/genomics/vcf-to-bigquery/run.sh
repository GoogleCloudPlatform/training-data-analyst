#!/bin/bash

bq_safe_mk() {
    dataset=$1
    exists=$(bq ls -d | grep -w $dataset)
    if [ -n "$exists" ]; then
       echo "Will write to table in $dataset"
    else
       echo "Creating $dataset"
       bq mk $dataset
    fi
}

if [ "$#" -ne 1 ]; then
    echo "Usage: ./run.sh  zone "
    echo "      eg: ./run.sh us-central1-f"
    exit
fi

ZONE=$1

# Hardcoded inputs. Change as necessary
BIGQUERY_DATASET=rice3k
BIGQUERY_TABLE=ERS467753
INPUT_VCF='gs://cloud-training-demos/genomics/rice_*.vcf'

# Create the BigQuery dataset
bq_safe_mk $BIGQUERY_DATASET

# Make a unique output bucket
YAML=vcf_bq.yaml
PROJECT_ID=$(gcloud config get-value project)
STAGING_BUCKET=gs://${PROJECT_ID}-${BIGQUERY_DATASET}-$(date +%s)
gsutil mb $STAGING_BUCKET
echo "Temporary files will be put into in $STAGING_BUCKET"

gcloud alpha genomics pipelines run \
    --project $PROJECT_ID \
    --pipeline-file $YAML \
    --logging gs://$STAGING_BUCKET/temp/runner_logs \
    --zones $ZONE \
    --service-account-scopes https://www.googleapis.com/auth/bigquery \
    --inputs `echo \
      PROJECT_ID="${PROJECT_ID}", \
      INPUT_VCF="${INPUT_VCF}", \
      BIGQUERY_DATASET="${BIGQUERY_DATASET}", \
      BIGQUERY_TABLE="${BIGQUERY_TABLE}", \
      STAGING_BUCKET="${STAGING_BUCKET}" \
      | tr -d '[:space:]'`

echo "Check the status using: "
echo "   gcloud alpha genomics operations describe  operations/...."
