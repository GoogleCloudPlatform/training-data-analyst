#!/bin/bash

INSTANCE_NAME=laktpu   # CHANGE THIS
GCP_LOGIN_NAME=vlakshmanan@google.com  # CHANGE THIS
ZONE=us-central1-b  # CHANGE THIS

TPU_NAME=$INSTANCE_NAME

gcloud config set compute/zone $ZONE

gcloud compute instances create $INSTANCE_NAME \
--machine-type n1-standard-2 \
--image-project deeplearning-platform-release \
--image-family tf-1-13-cpu \
--scopes cloud-platform \
--metadata proxy-user-mail="${GCP_LOGIN_NAME}",\
startup-script="echo export TPU_NAME=$TPU_NAME > /etc/profile.d/tpu-env.sh"

gcloud compute tpus create $TPU_NAME \
 --network default \
 --range 10.240.1.0 \
 --version 1.13
