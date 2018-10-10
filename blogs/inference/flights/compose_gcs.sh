#!/bin/bash

if [ "$#" -lt 1 ]; then
   echo "Usage:   ./compose_gcs.sh bucket "
   exit
fi

BUCKET=$1

gsutil compose gs://${BUCKET}/flights/json/sharded/flights_data* \
               gs://${BUCKET}/flights/json/flights_data.json

gsutil -m rm -rf gs://${BUCKET}/flights/json/sharded/
