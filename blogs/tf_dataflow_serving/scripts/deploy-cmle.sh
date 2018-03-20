#!/usr/bin/env bash

REGION="europe-west1"
BUCKET="ksalama-gcs-cloudml" # change to your bucket name

MODEL_NAME="babyweight_estimator" # change to your estimator name
MODEL_VERSION="v3" # change to your model version

gsutil -m cp -r model/trained/* gs://${BUCKET}/models/${MODEL_NAME}

MODEL_BINARIES=gs://${BUCKET}/models/${MODEL_NAME}/v1

gsutil ls ${MODEL_BINARIES}

# delete model version
gcloud ml-engine versions delete ${MODEL_VERSION} --model=${MODEL_NAME}

# delete model
gcloud ml-engine models delete ${MODEL_NAME}

# deploy model to GCP
gcloud ml-engine models create ${MODEL_NAME} --regions=${REGION}

# deploy model version
gcloud ml-engine versions create ${MODEL_VERSION} --model=${MODEL_NAME} --origin=${MODEL_BINARIES} --runtime-version=1.4