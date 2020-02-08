#!/bin/bash
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if [ "$#" -ne 4 ]; then
    echo "Usage: ./setup_auth.sh service-account-name zone cluster namespace"
    echo "     Get these values by visiting https://console.cloud.google.com/ai-platform/pipelines/clusters"
    echo "  eg:  ./setup_auth.sh kfpdemo us-central1-a cluster-1 default"
    exit
fi

PROJECT_ID=$(gcloud config get-value project)
SA_NAME=$1
ZONE=$2
CLUSTER=$3
NAMESPACE=$4


# See: https://github.com/kubeflow/pipelines/blob/master/manifests/gcp_marketplace/guide.md#gcp-service-account-credentials

gcloud container clusters get-credentials "$CLUSTER" --zone "$ZONE" --project "$PROJECT_ID"


# Create service account
gcloud iam service-accounts create $SA_NAME \
       --display-name $SA_NAME --project "$PROJECT_ID"

# Grant permissions to the service account by binding roles
# roles/editor is needed to launch a CAIP Notebook.
# The others (storage, bigquery, ml, dataflow) are pretty common for GCP ML pipelines
# That said, "admin" is a bit of an overkill; you might want to provide narrower roles for your users
for ROLE in roles/editor roles/storage.admin roles/bigquery.admin roles/ml.admin roles/dataflow.admin roles/pubsub.admin; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --role=$ROLE
done

# Create credential for the service account
gcloud iam service-accounts keys create application_default_credentials.json --iam-account $SA_NAME@$PROJECT_ID.iam.gserviceaccount.com

# Attempt to create a k8s secret. If already exists, override.
kubectl create secret generic user-gcp-sa \
  --from-file=user-gcp-sa.json=application_default_credentials.json \
  -n $NAMESPACE --dry-run -o yaml  |  kubectl apply -f -
  
# remove private key file
rm application_default_credentials.json
