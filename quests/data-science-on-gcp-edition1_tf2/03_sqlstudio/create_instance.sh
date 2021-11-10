#!/bin/bash
gcloud sql instances create flights \
    --tier=db-n1-standard-1 --activation-policy=ALWAYS --gce-zone=us-central1-a

echo "Please go to the GCP console and change the root password of the instance"
