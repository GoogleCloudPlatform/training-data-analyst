#!/bin/bash -e

# Copyright 2018 The Kubeflow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -x

KUBERNETES_NAMESPACE="${KUBERNETES_NAMESPACE:-kubeflow}"
NAME="my-deployment"

while (($#)); do
   case $1 in
     "--image")
       shift
       IMAGE_PATH="$1"
       shift
       ;;
     "--service-type")
       shift
       SERVICE_TYPE="$1"
       shift
       ;;
     "--container-port")
       shift
       CONTAINER_PORT="--containerPort=$1"
       shift
       ;;
     "--service-port")
       shift
       SERVICE_PORT="--servicePort=$1"
       shift
       ;;
     "--cluster-name")
       shift
       CLUSTER_NAME="$1"
       shift
       ;;
     "--namespace")
       shift
       KUBERNETES_NAMESPACE="$1"
       shift
       ;;
     "--name")
       shift
       NAME="$1"
       shift
       ;;
     *)
       echo "Unknown argument: '$1'"
       exit 1
       ;;
   esac
done

if [ -z "${IMAGE_PATH}" ]; then
  echo "You must specify an image to deploy"
  exit 1
fi

if [ -z "$SERVICE_TYPE" ]; then
    SERVICE_TYPE=ClusterIP
fi

echo "Deploying the image '${IMAGE_PATH}'"

if [ -z "${CLUSTER_NAME}" ]; then
  CLUSTER_NAME=$(wget -q -O- --header="Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/cluster-name)
fi

# Ensure the name is not more than 63 characters.
NAME="${NAME:0:63}"
# Trim any trailing hyphens from the server name.
while [[ "${NAME:(-1)}" == "-" ]]; do NAME="${NAME::-1}"; done

echo "Deploying ${NAME} to the cluster ${CLUSTER_NAME}"

# Connect kubectl to the local cluster
kubectl config set-cluster "${CLUSTER_NAME}" --server=https://kubernetes.default --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
kubectl config set-credentials pipeline --token "$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
kubectl config set-context kubeflow --cluster "${CLUSTER_NAME}" --user pipeline
kubectl config use-context kubeflow

# Configure and deploy the app
cd /src/github.com/kubeflow/kubeflow
git checkout ${KUBEFLOW_VERSION}

cd /opt
echo "Initializing KSonnet app..."
ks init tf-serving-app
cd tf-serving-app/

if [ -n "${KUBERNETES_NAMESPACE}" ]; then
  echo "Setting Kubernetes namespace: ${KUBERNETES_NAMESPACE} ..."
  ks env set default --namespace "${KUBERNETES_NAMESPACE}"
fi

ks generate deployed-service $NAME --name=$NAME --image=$IMAGE_PATH --type=$SERVICE_TYPE $CONTAINER_PORT $SERVICE_PORT

echo "Deploying the service..."
ks apply default -c $NAME

# Wait for the ip address
timeout="1000"
start_time=`date +%s`
PUBLIC_IP=""
while [ -z "$PUBLIC_IP" ]; do
  PUBLIC_IP=$(kubectl get svc -n $KUBERNETES_NAMESPACE $NAME -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2> /dev/null)
  current_time=`date +%s`
  elapsed_time=$(expr $current_time + 1 - $start_time)
  if [[ $elapsed_time -gt $timeout ]];then
    echo "timeout"
    exit 1
  fi
  sleep 5
done
echo "service active: $PUBLIC_IP"
