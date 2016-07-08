#!/bin/bash

sudo apt-get update
sudo apt-get install vim git curl wget unzip python-dev python-pip \
  libblas-dev liblapack-dev libatlas-base-dev gfortran
sudo pip install \
  setuptools \
  requests pyyaml google-api-python-client oauth2client==2.2.0 \
  numpy scikit-learn scipy pandas uritemplate \

# Install TensorFlow
sudo pip install "https://storage.googleapis.com/cloud-ml/tensorflow/debian/tensorflow-0.9.0-py2-none-any.whl"
