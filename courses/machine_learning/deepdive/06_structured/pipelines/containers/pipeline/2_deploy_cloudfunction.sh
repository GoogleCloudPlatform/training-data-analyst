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
    echo "Usage: ./2_deploy_cloudfunction.sh   cloudrun_url"
    echo "  eg:  ./2_deploy_cloudfunction.sh  https://kfpdemo-cbacefeq2a-uc.a.run.app"
    exit
fi


PROJECT=$(gcloud config get-value project)
BUCKET="${PROJECT}-kfpdemo"
CLOUDRUN_URL=$1

# Deploy Cloud Functions to monitor the bucket and invoke Cloud Run
gcloud functions deploy handle_newfile --runtime python37 \
    --set-env-vars DESTINATION_URL=${CLOUDRUN_URL} \
    --trigger-resource=${BUCKET} --trigger-event=google.storage.object.finalize