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

gsutil mb $KOPS_STORE

n=0
until [ $n -ge 5 ]
do
    gsutil ls | grep $KOPS_STORE && break
    n=$[$n+1]
    sleep 3
done

export KOPS_FEATURE_FLAGS=AlphaAllowGCE

kops create cluster \
--name=$C2_FULLNAME \
--zones=$KOPS_ZONES \
--state=$KOPS_STORE \
--project=${PROJECT_ID} \
--node-count=$NODE_COUNT \
--node-size=$NODE_SIZE \
--admin-access=$INSTANCE_CIDR \
--yes

for (( c=1; c<=20; c++))
do
	echo "Check if cluster is ready - Attempt $c"
        CHECK=`kops validate cluster --name $C2_FULLNAME --state $KOPS_STORE | grep ready | wc -l`
        if [[ "$CHECK" == "1" ]]; then
                break;
        fi
        sleep 10
done

sleep 20


kops export kubecfg --name $C2_FULLNAME --state=$KOPS_STORE
gsutil cp ~/.kube/config $KOPS_STORE

gcloud iam service-accounts create connect-sa-op

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
 --member="serviceAccount:connect-sa-op@${PROJECT_ID}.iam.gserviceaccount.com" \
 --role="roles/gkehub.connect"

gcloud iam service-accounts keys create connect-sa-op-key.json \
  --iam-account=connect-sa-op@${PROJECT_ID}.iam.gserviceaccount.com

gcloud container hub memberships register ${C2_NAME}-connect \
   --context=$C2_FULLNAME \
   --service-account-key-file=./connect-sa-op-key.json \
   --project=$PROJECT_ID

export KSA=remote-admin-sa
kubectl create serviceaccount $KSA
kubectl create clusterrolebinding ksa-admin-binding \
    --clusterrole cluster-admin \
    --serviceaccount default:$KSA

ISTIO_VERSION="${ISTIO_VERSION:-1.5.2}"
curl -L https://git.io/getLatestIstio | ISTIO_VERSION=$ISTIO_VERSION sh -

kubectl create namespace istio-system
kubectl create secret generic cacerts -n istio-system \
--from-file=istio-$ISTIO_VERSION/samples/certs/ca-cert.pem \
--from-file=istio-$ISTIO_VERSION/samples/certs/ca-key.pem \
--from-file=istio-$ISTIO_VERSION/samples/certs/root-cert.pem \
--from-file=istio-$ISTIO_VERSION/samples/certs/cert-chain.pem

./istio-$ISTIO_VERSION/bin/istioctl manifest apply \
--set profile=demo

kubectl create namespace prod
kubectl label namespace prod istio-injection=enabled --overwrite
kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/kubernetes-manifests.yaml
kubectl apply -n prod-f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/istio-manifests.yaml
kubectl patch -n prod deployments/productcatalogservice -p '{"spec":{"template":{"metadata":{"labels":{"version":"v1"}}}}}'
