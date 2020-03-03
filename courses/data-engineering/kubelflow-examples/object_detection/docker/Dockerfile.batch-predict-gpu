# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.#

ARG base_image=tensorflow/tensorflow:1.8.0-gpu

FROM $base_image

MAINTAINER Yixin Shi <yxshi@google.com>

RUN     apt-get update && apt-get install -y software-properties-common && \
        add-apt-repository ppa:ubuntu-toolchain-r/test -y && \
        apt-get update && apt-get install -y \
        build-essential \
        curl \
        libcurl3-dev \
        git \
        libfreetype6-dev \
        libpng12-dev \
        libzmq3-dev \
        pkg-config \
        python-dev \
        python-numpy \
        python-pip \
        swig \
        zip \
        zlib1g-dev \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /root

RUN pip install -U setuptools && \
  curl -o /tmp/kubeflow-batch-predict.zip -L https://github.com/kubeflow/batch-predict/archive/master.zip && \
  mkdir -p /tmp/unzipped && \
  unzip -o /tmp/kubeflow-batch-predict.zip -d /tmp/unzipped && \
  sed -i 's/tensorflow/tensorflow-gpu/g' /tmp/unzipped/batch-predict-master/kubeflow_batch_predict/version.py && \
  cd /tmp/unzipped && \
  zip -r /opt/kubeflow-batch-predict.zip * && \
  pip install /opt/kubeflow-batch-predict.zip && \
  pip install apache-beam[gcp]==2.3.0 && \
  rm -rf /tmp/unzipped && \
  rm -rf /root/.cache/pip;

ENTRYPOINT [ "python", "-m", "kubeflow_batch_predict.dataflow.batch_prediction_main" ]
