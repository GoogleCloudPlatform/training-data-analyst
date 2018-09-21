#!/bin/bash

if [ "$#" -lt 1 ]; then
   echo "Usage:   ./bq_to_json.sh BUCKET "
   exit
fi

BUCKET=$1


bq extract --destination_format NEWLINE_DELIMITED_JSON cloud-training-demos:flights.tzcorr gs://${BUCKET}/flights/flights_data*.json
