#!/bin/bash
#gsutil cp gs://cloud-datalab/datalab-server-no-websockets.yaml  datalab.yaml

# Remove "_" from USER because "_" can not be used for instance name
INSTANCE_NAME=${USER//_/}

gcloud compute instances create datalabvm-${INSTANCE_NAME} \
   --image-family=container-vm --image-project=google-containers \
   --zone us-central1-a --machine-type n1-standard-1 \
   --metadata "google-container-manifest=$(cat datalab.yaml)" \
   --scopes cloud-platform
