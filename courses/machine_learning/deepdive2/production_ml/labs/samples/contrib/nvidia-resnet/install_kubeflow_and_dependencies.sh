#!/bin/bash
# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Install nvidia-docker 2
sudo tee /etc/docker/daemon.json <<EOF
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
EOF
sudo pkill -SIGHUP dockerd

# Install MiniKube
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 \
  && chmod +x minikube
sudo cp minikube /usr/local/bin && rm minikube

# Install kubectl
sudo apt-get update && sudo apt-get install -y apt-transport-https
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo touch /etc/apt/sources.list.d/kubernetes.list
echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl

# Install ksonnet
export KS_VER=0.13.1
wget --no-verbose https://github.com/ksonnet/ksonnet/releases/download/v${KS_VER}/ks_${KS_VER}_linux_amd64.tar.gz -O ksonnet.tar.gz
mkdir -p ksonnet
tar -xf ksonnet.tar.gz -C ksonnet --strip-components=1
sudo cp ksonnet/ks /usr/local/bin
rm -fr ksonnet
rm ksonnet.tar.gz

# Start Minikube
sudo minikube start --vm-driver=none --extra-config=kubelet.resolv-conf=/run/systemd/resolve/resolv.conf

# Add the NVIDIA device plugin
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v1.11/nvidia-device-plugin.yml

# Install Kubeflow
export KUBEFLOW_SRC=/tmp/kubeflow
export KFAPP=kfapp
mkdir ${KUBEFLOW_SRC}
cd ${KUBEFLOW_SRC}
export KUBEFLOW_TAG=v0.4.1
curl https://raw.githubusercontent.com/kubeflow/kubeflow/${KUBEFLOW_TAG}/scripts/download.sh | bash
KUBEFLOW_REPO=${KUBEFLOW_SRC} ${KUBEFLOW_SRC}/scripts/kfctl.sh init ${KFAPP} --platform minikube
cd ${KFAPP}
${KUBEFLOW_SRC}/scripts/kfctl.sh generate all
${KUBEFLOW_SRC}/scripts/kfctl.sh apply all

# Open up ambassador’s port
kubectl patch svc ambassador -n kubeflow --type='json' -p '[{"op":"replace","path":"/spec/type","value":"NodePort"}]'
