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

source ./scripts/env.sh

gcloud config set compute/zone ${C1_ZONE}
gcloud beta container clusters create ${C1_NAME} \
    --machine-type=n1-standard-4 \
    --num-nodes=4 \
    --workload-pool=${WORKLOAD_POOL} \
    --enable-stackdriver-kubernetes \
    --subnetwork=default \
    --labels mesh_id=${MESH_ID} \
    --release-channel=regular

# service account requires additional role bindings
kubectl create clusterrolebinding [BINDING_NAME] \
    --clusterrole cluster-admin --user [USER]

gcloud iam service-accounts create connect-sa

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
 --member="serviceAccount:connect-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
 --role="roles/gkehub.connect"

gcloud iam service-accounts keys create connect-sa-key.json \
  --iam-account=connect-sa@${PROJECT_ID}.iam.gserviceaccount.com

gcloud container hub memberships register ${C1_NAME}-connect \
   --gke-cluster=${C1_ZONE}/${C1_NAME}  \
   --service-account-key-file=./connect-sa-key.json

# config project for Anthos Service Mesh
curl --request POST \
  --header "Authorization: Bearer $(gcloud auth print-access-token)" \
  --data '' \
  https://meshconfig.googleapis.com/v1alpha1/projects/${PROJECT_ID}:initialize


curl -LO https://storage.googleapis.com/gke-release/asm/istio-1.6.8-asm.9-linux-amd64.tar.gz
tar xzf istio-1.6.8-asm.9-linux-amd64.tar.gz
cd istio-1.6.8-asm.9
export PATH=$PWD/bin:$PATH

kpt pkg get https://github.com/GoogleCloudPlatform/anthos-service-mesh-packages@1.6.8-asm.9 asm

cd asm
kpt cfg set asm gcloud.container.cluster ${C1_NAME}
kpt cfg set asm gcloud.project.environProjectNumber ${PROJECT_NUMBER}
kpt cfg set asm gcloud.core.project ${PROJECT_ID}
kpt cfg set asm gcloud.compute.location ${C1_ZONE}

# To configure that all clusters are in the same project
kpt cfg set asm anthos.servicemesh.profile asm-gcp

gcloud container clusters get-credentials $C1_NAME \
    --zone $C1_ZONE --project $PROJECT_ID

# Install Istio + Enable tracing with Cloud Trace
istioctl install -f asm/cluster/istio-operator.yaml -f $LAB_DIR/training-data-analyst/courses/ahybrid/v1.0/AHYBRID050/scripts/tracing.yaml

# Enable the Anthos Service Mesh UI in Cloud Console
kubectl apply -f asm/canonical-service/controller.yaml

kubectl wait --for=condition=available --timeout=600s deployment \
  --all -n istio-system

kubectl label namespace default istio-injection=enabled --overwrite

# Deploy BookInfo application
kubectl apply -f ../samples/bookinfo/platform/kube/bookinfo.yaml

# Sleep while Bookinfo pods initialize
sleep 30s

# Expose Bookinfo external gateway/IP
kubectl apply -f ../samples/bookinfo/networking/bookinfo-gateway.yaml