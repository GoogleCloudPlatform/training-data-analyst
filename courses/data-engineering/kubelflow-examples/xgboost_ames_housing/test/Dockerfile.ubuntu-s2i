# This file builds an docker image that has source-to-image tool `s2i` installed

FROM ubuntu:xenial

Run set -ex && \
    apt-get update -yqq && \
    apt-get install -yqq --no-install-recommends \
    wget \
    ca-certificates

# Install s2i
RUN cd /tmp && \
    wget -O s2i.tar.gz https://github.com/openshift/source-to-image/releases/download/v1.1.13/source-to-image-v1.1.13-b54d75d3-linux-amd64.tar.gz && \
    tar -xvf s2i.tar.gz && \
    mv ./s2i /usr/local/bin
