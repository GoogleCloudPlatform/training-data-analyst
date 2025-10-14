#!/bin/bash

if [ "$#" -lt 1 ]; then
   echo "Usage:   ./compose_gcs.sh bucket "
   exit
fi

BUCKET=$1

gcloud storage objects compose gs://${BUCKET}/flights/json/sharded/flights_data* \
               gs://${BUCKET}/flights/json/flights_data.json

gcloud storage rm --recursive --continue-on-error gs://${BUCKET}/flights/json/sharded/
