# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

FROM gcr.io/kubeflow-images-public/tensorflow-1.8.0-notebook-cpu

ENV KS_VER=0.12.0 KS_ARCH=linux_amd64

RUN apt-get update && apt-get install -y python-pip &&\
    curl -LO "https://github.com/ksonnet/ksonnet/releases/download/v${KS_VER}/ks_${KS_VER}_${KS_ARCH}.tar.gz" &&\
    tar -xvf ks_*.tar.gz && \
    cp ks_*/ks /usr/local/bin &&\
    rm -rf ks_*

RUN pip install --no-cache-dir annoy ktext nltk Pillow pydot
