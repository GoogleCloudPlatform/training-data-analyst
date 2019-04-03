#!/bin/bash

INSTANCE_NAME=tfgpu   # CHANGE THIS
GCP_LOGIN_NAME=vlakshmanan@google.com  # CHANGE THIS
ZONE="us-west1-b" # CHANGE THIS
INSTANCE_TYPE="n1-standard-4" # CHANGE THIS

#IMAGE_FAMILY=tf-1-12-cu100
IMAGE_FAMILY=tf-1-13-cu100

gcloud compute instances create ${INSTANCE_NAME} \
      --machine-type=$INSTANCE_TYPE \
      --zone=$ZONE \
      --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email \
      --min-cpu-platform="Intel Skylake" \
      --image-family="$IMAGE_FAMILY" \
      --image-project=deeplearning-platform-release \
      --boot-disk-size=100GB \
      --boot-disk-type=pd-ssd \
      --accelerator=type=nvidia-tesla-p100,count=1 \
      --boot-disk-device-name=${INSTANCE_NAME} \
      --maintenance-policy=TERMINATE --restart-on-failure \
      --metadata="proxy-user-mail=${GCP_LOGIN_NAME},install-nvidia-driver=True"
