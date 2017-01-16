#!/bin/bash

ZONE=us-central1-a
gcloud compute ssh  --zone=$ZONE  \
  --ssh-flag="-D 1080" --ssh-flag="-N" --ssh-flag="-n" \
  ch6cluster-m
