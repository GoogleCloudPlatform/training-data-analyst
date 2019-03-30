#!/bin/bash

INSTANCE_NAME=tfxdemo   # CHANGE THIS
GCP_LOGIN_NAME=vlakshmanan@google.com  # CHANGE THIS
ZONE="us-west1-b" # CHANGE THIS
INSTANCE_TYPE="n1-standard-4" # CHANGE THIS

IMAGE_FAMILY=tf-latest-cpu

gcloud compute instances create ${INSTANCE_NAME} \
      --machine-type=$INSTANCE_TYPE \
      --zone=$ZONE \
      --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email \
      --min-cpu-platform="Intel Skylake" \
      --image-family="$IMAGE_FAMILY" \
      --image-project=deeplearning-platform-release \
      --boot-disk-size=100GB \
      --boot-disk-type=pd-ssd \
      --boot-disk-device-name=${INSTANCE_NAME} \
      --maintenance-policy=TERMINATE --restart-on-failure \
      --metadata="proxy-user-mail=${GCP_LOGIN_NAME}"

echo "Looking for Jupyter URL on $INSTANCE_NAME"
while true; do
   proxy=$(gcloud compute instances describe --zone $ZONE ${INSTANCE_NAME} 2> /dev/null | grep dot-datalab-vm)
   if [ -z "$proxy" ]
   then
      echo -n "."
      sleep 1
   else
      echo "done!"
      echo "$proxy"
      break
   fi
done

