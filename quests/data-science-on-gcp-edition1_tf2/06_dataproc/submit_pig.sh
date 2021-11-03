#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./submit_pig.sh  region"
    exit
fi

REGION=$1

gsutil -m rm -r gs://cloud-training-demos-ml/flights/pigoutput
gcloud dataproc jobs submit pig --cluster ch6cluster --region $REGION --file $*
