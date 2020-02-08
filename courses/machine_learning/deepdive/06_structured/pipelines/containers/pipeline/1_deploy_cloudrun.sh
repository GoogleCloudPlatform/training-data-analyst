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
    echo "Usage: ./1_deploy_cloudrun.sh pipelines_host"
    echo "  eg:  ./1_deploy_cloudrun.sh 447cdd24f70c9541-dot-us-central1.notebooks.googleusercontent.com"
    exit
fi

PROJECT=$(gcloud config get-value project)
PIPELINES_HOST=$1
BUCKET="${PROJECT}-kfpdemo"

# setup Pub/Sub topic for changes to bucket
TOPIC="projects/${PROJECT}/topics/bucket-${BUCKET}"
gsutil notification create -t ${TOPIC} -f json -e OBJECT_FINALIZE gs://${BUCKET} || true

# deploy Cloud Run
gcloud run deploy kfpdemo --platform=managed --region=us-central1 \
   --image gcr.io/${PROJECT}/babyweight-pipeline-pipeline \
   --set-env-vars=PROJECT=${PROJECT},BUCKET=${BUCKET},PIPELINES_HOST=${PIPELINES_HOST}
