#!/usr/bin/env bash

#[START deploy_cmle]

PROJECT="[PROJECT_ID]" # change to your project name
REGION="[REGION]"
BUCKET="[BUCKET]" # change to your bucket name
MODEL_NAME="babyweight_estimator" # change to your estimator name
MODEL_VERSION="v1" # change to your model version
MODEL_BINARIES=gs://${BUCKET}/models/${MODEL_NAME}

# upload the local SavedModel to GCS
gsutil -m cp -r model/trained/v1/* gs://${BUCKET}/models/${MODEL_NAME}

# set the current project
gcloud config set project ${PROJECT}

# list model files on GCS
gsutil ls ${MODEL_BINARIES}

# deploy model to GCP
gcloud ml-engine models create ${MODEL_NAME} --regions=${REGION}

# deploy model version
gcloud ml-engine versions create ${MODEL_VERSION} --model=${MODEL_NAME} --origin=${MODEL_BINARIES} --runtime-version=1.4

#[END deploy_cmle]
