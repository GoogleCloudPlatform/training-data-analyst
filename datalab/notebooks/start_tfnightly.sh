#!/bin/bash

INSTANCE_NAME=laktfnightly   # CHANGE THIS
GCP_LOGIN_NAME=vlakshmanan@google.com  # CHANGE THIS
ZONE="us-west1-b" # CHANGE THIS
INSTANCE_TYPE="n1-standard-4" # CHANGE THIS

gcloud compute instances create ${INSTANCE_NAME} \
      --machine-type=$INSTANCE_TYPE \
      --zone=$ZONE \
      --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email \
      --min-cpu-platform="Intel Skylake" \
      --image-family="tf-latest-gpu-experimental" \
      --image-project=deeplearning-platform-release \
      --boot-disk-size=100GB \
      --boot-disk-type=pd-ssd \
      --accelerator=type=nvidia-tesla-p100,count=1 \
      --boot-disk-device-name=${INSTANCE_NAME} \
      --maintenance-policy=TERMINATE --restart-on-failure \
      --metadata="proxy-user-mail=${GCP_LOGIN_NAME},install-nvidia-driver=True"

