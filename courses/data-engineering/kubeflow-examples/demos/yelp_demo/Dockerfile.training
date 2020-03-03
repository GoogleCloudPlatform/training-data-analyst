# For GPU use gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-gpu:latest
# For CPU use gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-cpu:latest
ARG BASE_IMAGE=gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-gpu:latest

FROM $BASE_IMAGE

USER root

RUN apt-get install -y jq

RUN curl https://sdk.cloud.google.com | bash

USER jovyan

RUN pip install oauth2client tensor2tensor h5py

COPY . /home/jovyan/yelp_sentiment
