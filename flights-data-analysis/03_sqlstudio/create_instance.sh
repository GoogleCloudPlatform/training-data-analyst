#!/bin/bash
gcloud sql instances create flights \
    --tier=db-n1-standard-1 --activation-policy=ALWAYS
