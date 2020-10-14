#!/usr/bin/env bash

# Copyright 2019 Google LLC
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

source ./scripts/env.sh

echo "### "
echo "### Begin Provision GKE"
echo "### "

gcloud config set compute/zone ${C1_ZONE}
gcloud beta container clusters create ${C1_NAME} \
    --machine-type "n1-standard-4" \
    --image-type "COS" \
    --disk-size "100" \
    --scopes "https://www.googleapis.com/auth/compute","https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
    --num-nodes "2" \
    --enable-autoscaling --min-nodes 2 --max-nodes 8 \
    --network "default" \
    --enable-ip-alias \
    --workload-pool=${WORKLOAD_POOL} \
    --enable-stackdriver-kubernetes \
    --release-channel=regular

# service account requires additional role bindings
kubectl create clusterrolebinding [BINDING_NAME] \
    --clusterrole cluster-admin --user [USER]

echo "### "
echo "### Provision GKE complete"
echo "### "
