#!/bin/bash -e
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

if [ "$#" -ne 1 ]; then
    echo "Usage: ./2_connect_cloudrun.sh cloudrun_url"
    echo "  eg:  ./2_connect_cloudrun.sh https://kfpdemo-cbacefeq2a-uc.a.run.app"
    exit
fi

PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud compute project-info describe --format='value(id)')
CLOUDRUN_URL=$1
BUCKET="${PROJECT_ID}-kfpdemo"

# setup Pub/Sub topic for changes to bucket
TOPIC="projects/${PROJECT_ID}/topics/bucket-${BUCKET}"
gsutil notification delete gs://${BUCKET} || true
gsutil notification create -t ${TOPIC} -f json -e OBJECT_FINALIZE gs://${BUCKET}
     
# create service account to represent pub/sub and give it permission
gcloud iam service-accounts create cloud-run-pubsub-invoker \
     --display-name "Cloud Run Pub/Sub Invoker" || true

gcloud run  \
   services add-iam-policy-binding kfpdemo \
   --platform=managed --region=us-central1 \
   --member=serviceAccount:cloud-run-pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
   --role=roles/run.invoker

# create a subscription
gcloud pubsub subscriptions create kfpdemoCloudRunSubscription --topic ${TOPIC} \
   --push-endpoint=${CLOUDRUN_URL}/ \
   --push-auth-service-account=cloud-run-pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com
   