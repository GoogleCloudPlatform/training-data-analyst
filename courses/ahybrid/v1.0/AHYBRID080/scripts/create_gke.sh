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

# create the gke cluster
gcloud config set compute/zone ${C1_ZONE}
gcloud beta container clusters create ${C1_NAME} \
    --machine-type=n1-standard-4 \
    --num-nodes=2 \
    --workload-pool=${WORKLOAD_POOL} \
    --enable-stackdriver-kubernetes \
    --subnetwork=default \
    --labels mesh_id=${MESH_ID}
    --release-channel=regular

# service account requires additional role bindings
kubectl create clusterrolebinding [BINDING_NAME] \
    --clusterrole cluster-admin --user [USER]

# create the service account for gke-connect
gcloud iam service-accounts create connect-sa

# assign GSA the role it needs
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
 --member="serviceAccount:connect-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
 --role="roles/gkehub.connect"

# download the service account key
gcloud iam service-accounts keys create connect-sa-key.json \
  --iam-account=connect-sa@${PROJECT_ID}.iam.gserviceaccount.com

# register the cluster
gcloud container hub memberships register ${C1_NAME}-connect \
   --gke-cluster=${C1_ZONE}/${C1_NAME}  \
   --service-account-key-file=./connect-sa-key.json

# config project for Anthos Service Mesh
curl --request POST \
  --header "Authorization: Bearer $(gcloud auth print-access-token)" \
  --data '' \
  https://meshconfig.googleapis.com/v1alpha1/projects/${PROJECT_ID}:initialize

# download anthos service mesh software
curl -LO https://storage.googleapis.com/gke-release/asm/istio-1.4.7-asm.0-linux.tar.gz
tar xzf istio-1.4.7-asm.0-linux.tar.gz


./istio-1.4.7-asm.0/bin/istioctl manifest apply --set profile=asm \
 --set values.global.trustDomain=${WORKLOAD_POOL} \
 --set values.global.sds.token.aud=${WORKLOAD_POOL} \
 --set values.nodeagent.env.GKE_CLUSTER_URL=https://container.googleapis.com/v1/projects/${PROJECT_ID}/locations/${C1_ZONE}/clusters/${C1_NAME} \
 --set values.global.meshID=${MESH_ID} \
 --set values.global.proxy.env.GCP_METADATA="${PROJECT_ID}|${PROJECT_NUMBER}|${C1_NAME}|${C1_ZONE}" \
 --set values.tracing.enabled=true \
 --set values.global.proxy.tracer="stackdriver"

kubectl wait --for=condition=available --timeout=600s deployment \
--all -n istio-system

kubectl create namespace prod
kubectl label namespace prod istio-injection=enabled --overwrite
kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/kubernetes-manifests.yaml
kubectl apply -n prod-f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/istio-manifests.yaml
kubectl patch -n prod deployments/productcatalogservice -p '{"spec":{"template":{"metadata":{"labels":{"version":"v1"}}}}}'
