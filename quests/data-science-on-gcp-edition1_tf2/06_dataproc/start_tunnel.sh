#!/bin/bash

ZONE=us-central1-a
PROJECT=$(gcloud config get-value project)
gcloud compute ssh  --zone=$ZONE --project=${PROJECT} \
  ch6cluster-m \
  -- \
  -D 1080 -N
