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

gcloud storage buckets create $KOPS_STORE

n=0
until [ $n -ge 5 ]
do
    gcloud storage ls | grep $KOPS_STORE && break
    n=$[$n+1]
    sleep 3
done

export K8S_VERSION="1.25.4"

echo "Creating the remote cluster..."
kops create cluster \
--name=$C2_FULLNAME \
--zones=$KOPS_ZONES \
--state=$KOPS_STORE \
--project=${PROJECT_ID} \
--node-count=$NODE_COUNT \
--node-size=$NODE_SIZE \
--admin-access=$INSTANCE_CIDR \
--kubernetes-version=$K8S_VERSION \
--yes

for (( c=1; c<=40; c++))
do
	echo "Check if cluster is ready - Attempt $c"
  CHECK=`kops validate cluster --name $C2_FULLNAME --state $KOPS_STORE | grep ready | wc -l`
  if [[ "$CHECK" == "1" ]]; then
    echo "Cluster is ready!"
    break;
  fi
  sleep 10
done

sleep 20

# SEE WHERE WE ARE HERE...
if [[ -f ".kube/config" ]]
then
  export KF=".kube/config"
else
  export KF="/root/.kube/config"
fi

echo "copying the kubeconfig file for later use..."
kops export kubecfg --name $C2_FULLNAME --state=$KOPS_STORE
gcloud storage cp $KF $KOPS_STORE

echo "creating service account and granting role..."
gcloud iam service-accounts create connect-sa-op

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
 --member="serviceAccount:connect-sa-op@${PROJECT_ID}.iam.gserviceaccount.com" \
 --role="roles/gkehub.connect"

gcloud iam service-accounts keys create connect-sa-op-key.json \
  --iam-account=connect-sa-op@${PROJECT_ID}.iam.gserviceaccount.com

kubectl config view

echo "registering the remote cluster"
gcloud container fleet memberships register ${C2_NAME}-connect \
   --context=$C2_FULLNAME \
   --service-account-key-file=./connect-sa-op-key.json \
   --project=$PROJECT_ID \
   --kubeconfig $KF

echo "creating a clusterrolebinding"
export KSA=remote-admin-sa
kubectl create serviceaccount $KSA
kubectl create clusterrolebinding ksa-admin-binding \
    --clusterrole cluster-admin \
    --serviceaccount default:$KSA
