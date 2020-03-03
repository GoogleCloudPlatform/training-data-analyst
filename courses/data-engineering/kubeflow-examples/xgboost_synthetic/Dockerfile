# Create docker image for the demo
#
# This docker image is based on existing notebook image
# It also includes the dependencies required for training and deploying
# this way we can use it as the base image
# Note: when using ClusterBuilder I believe the base image gets over written
FROM gcr.io/kubeflow-images-public/tensorflow-1.14.0-notebook-cpu:v0.7.0

COPY requirements.txt .

# We want to install the requirements in the system directory so we need to switch to root
USER root
RUN pip3 --no-cache-dir install -r requirements.txt
USER jovyan
