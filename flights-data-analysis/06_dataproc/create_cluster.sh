#!/bin/bash

gcloud dataproc clusters create --bucket=cloud-training-demos-ml --num-workers=2 --scopes=cloud-platform --worker-machine-type=n1-standard-2 --master-machine-type=n1-standard-2 --zone=us-central1-a ch6cluster
