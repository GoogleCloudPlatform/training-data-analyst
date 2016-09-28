#!/bin/bash
gsutil cp gs://cloud-datalab/datalab-server-no-websockets.yaml  datalab.yaml
gcloud compute instances create datalabvm-${USER} \
   --image-family=container-vm --image-project=google-containers \
   --zone us-central1-a --machine-type n1-standard-1 \
   --metadata "google-container-manifest=$(cat datalab.yaml)" \
   --scopes cloud-platform
