# Copyright 2018 Intel Corporation.
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
# limitations under the License.

FROM ubuntu:16.04

LABEL maintainer="Soila Kavulya <soila.p.kavulya@intel.com>"

# Pick up some TF dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libfreetype6-dev \
        libpng12-dev \
        libzmq3-dev \
        pkg-config \
        python \
        python-dev \
        python-pil \
        python-tk \
        python-lxml \
        rsync \
        git \
        software-properties-common \
        unzip \
        wget \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -O https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py && \
    rm get-pip.py

RUN pip --no-cache-dir install \
        tensorflow==1.10.0

RUN pip --no-cache-dir install \
        Cython \
        contextlib2 \
        jupyter \
        matplotlib

# Setup Universal Object Detection
ENV MODELS_HOME "/models"
RUN git clone https://github.com/tensorflow/models.git $MODELS_HOME

RUN cd $MODELS_HOME/research && \
    wget -O protobuf.zip https://github.com/google/protobuf/releases/download/v3.0.0/protoc-3.0.0-linux-x86_64.zip && \
    unzip protobuf.zip && \
    ./bin/protoc object_detection/protos/*.proto --python_out=.

RUN git clone https://github.com/cocodataset/cocoapi.git && \
    cd cocoapi/PythonAPI && \
    make && \
    cp -r pycocotools $MODELS_HOME/research

ENV PYTHONPATH "$MODELS_HOME/research:$MODELS_HOME/research/slim:$PYTHONPATH"

# TensorBoard
EXPOSE 6006

WORKDIR $MODELS_HOME

# Run training job
ARG pipeline_config_path
ARG train_dir

CMD ["python", "$MODELS_HOME/research/object_detection/legacy/train.py", "--pipeline_config_path=$pipeline_config_path"  "--train_dir=$train_dir"]
