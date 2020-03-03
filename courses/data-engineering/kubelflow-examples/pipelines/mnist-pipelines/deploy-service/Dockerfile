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

FROM debian

RUN apt-get update -q && apt-get upgrade -y && \
    apt-get install -y -qq --no-install-recommends \
      apt-transport-https \
      ca-certificates \
      git \
      gnupg \
      lsb-release \
      unzip \
      wget && \
    wget -O /opt/ks_0.12.0_linux_amd64.tar.gz \
      https://github.com/ksonnet/ksonnet/releases/download/v0.12.0/ks_0.12.0_linux_amd64.tar.gz && \
    tar -C /opt -xzf /opt/ks_0.12.0_linux_amd64.tar.gz && \
    cp /opt/ks_0.12.0_linux_amd64/ks /bin/. && \
    rm -f /opt/ks_0.12.0_linux_amd64.tar.gz && \
    wget -O /bin/kubectl \
      https://storage.googleapis.com/kubernetes-release/release/v1.11.2/bin/linux/amd64/kubectl && \
    chmod u+x /bin/kubectl && \
    wget -O /opt/kubernetes_v1.11.2 \
      https://github.com/kubernetes/kubernetes/archive/v1.11.2.tar.gz && \
    mkdir -p /src && \
    tar -C /src -xzf /opt/kubernetes_v1.11.2 && \
    rm -rf /opt/kubernetes_v1.11.2 && \
    wget -O /opt/google-apt-key.gpg \
      https://packages.cloud.google.com/apt/doc/apt-key.gpg && \
    apt-key add /opt/google-apt-key.gpg && \
    export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb https://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" >> \
      /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update -q && \
    apt-get install -y -qq --no-install-recommends google-cloud-sdk && \
    gcloud config set component_manager/disable_update_check true

ENV KUBEFLOW_VERSION v0.2.5

# Checkout the kubeflow packages at image build time so that we do not
# require calling in to the GitHub API at run time.
RUN cd /src && \
    mkdir -p github.com/kubeflow && \
    cd github.com/kubeflow && \
    git clone https://github.com/kubeflow/kubeflow && \
    cd kubeflow && \
    git checkout ${KUBEFLOW_VERSION}

ADD ./src/deploy.sh /bin/.

ENTRYPOINT ["/bin/deploy.sh"]
