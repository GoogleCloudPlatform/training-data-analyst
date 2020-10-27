# https://github.com/theia-ide/theia-apps/blob/master/theia-java-docker/Dockerfile
FROM theiaide/theia-python:latest

RUN curl -sSL https://sdk.cloud.google.com | bash

USER root

RUN apt-get update && apt-get install -y python3-pip

RUN /usr/bin/python3 -m pip install --upgrade pip
RUN /usr/bin/python3 -m pip install anytree google-cloud-pubsub faker geocoder


USER theia

ENV PATH $PATH:/root/google-cloud-sdk/bin:/home/theia/google-cloud-sdk/bin