#!/usr/bin/env bash

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

# general values
export PATH=$PATH:$LAB_DIR/bin:
export PROJECT_ID=$(gcloud config get-value project)

# gke cluster values
export C1_NAME="gke"
export C1_ZONE="us-central1-b"
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} \
    --format="value(projectNumber)")
export WORKLOAD_POOL=${PROJECT_ID}.svc.id.goog
export MESH_ID="proj-${PROJECT_NUMBER}"

# on-prem cluster values
export C2_NAME="onprem"
export C2_FULLNAME=$C2_NAME.k8s.local
export C2_ZONE="us-east1-b"
export NODE_COUNT=2
export NODE_SIZE=n1-standard-2
export KOPS_ZONES=$C2_ZONE
export INSTANCE_IP=$(curl -s api.ipify.org)
export INSTANCE_CIDR=$INSTANCE_IP/32
export KOPS_STORE=gs://$PROJECT_ID-kops-$C2_NAME

