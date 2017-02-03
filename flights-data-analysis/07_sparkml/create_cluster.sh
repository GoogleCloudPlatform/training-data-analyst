#!/bin/bash

ZONE=us-central1-a

# create cluster
gcloud dataproc clusters create \
   --num-workers=30 \
   --num-preemptible-workers=5 \
   --scopes=cloud-platform \
   --worker-machine-type=n1-standard-4 \
   --master-machine-type=n1-standard-8 \
   --worker-boot-disk-size=10 \
   --preemptible-worker-boot-disk-size=10 \
   --zone=$ZONE \
   ch6cluster
