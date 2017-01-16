#!/bin/bash

ZONE=us-central1-a
gcloud compute ssh  --zone=$ZONE  \
  --ssh-flag="-N" --ssh-flag="-L" \
  --ssh-flag="localhost:8081:localhost:8080" \
  ch6cluster-m
