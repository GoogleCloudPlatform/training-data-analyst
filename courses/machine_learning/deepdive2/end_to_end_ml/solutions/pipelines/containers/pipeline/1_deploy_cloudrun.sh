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

if [ "$#" -ne 2 ]; then
    echo "Usage: ./1_deploy_cloudrun.sh pipelines_host hparam_job_name"
    echo "  eg:  ./1_deploy_cloudrun.sh 447cdd24f70c9541-dot-us-central1.notebooks.googleusercontent.com  babyweight_200207_231639"
    exit
fi


PROJECT=$(gcloud config get-value project)
BUCKET="${PROJECT}-kfpdemo"
REGION=us-central1
PIPELINES_HOST=$1
HPARAM_JOB=$2

# build the container for Cloud Run
../build_container.sh

# deploy Cloud Run
gcloud run deploy kfpdemo \
   --platform=managed --region=${REGION} \
   --image gcr.io/${PROJECT}/babyweight-pipeline-pipeline \
   --set-env-vars PROJECT=${PROJECT},BUCKET=${BUCKET},PIPELINES_HOST=${PIPELINES_HOST},HPARAM_JOB=${HPARAM_JOB}

