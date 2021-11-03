#!/bin/sh

if [ "$#" -ne 1 ]; then
    echo "Usage: ./load_to_bq.sh  bucket-name"
    exit
fi
PROJECT=$DEVSHELL_PROJECT_ID
BUCKET=$1

bq show --format=prettyjson flights.simevents > simevents.json

ONE_FILE=$(gsutil ls gs://${BUCKET}/flights/tzcorr/all_flights-00001*)
echo "Creating table definition from $ONE_FILE"
bq mk --external_table_definition=./tzcorr.json@CSV=$ONE_FILE flights.fedtzcorr

echo "Loading all files into BigQuery"
bq load flights.tzcorr "gs://${BUCKET}/flights/tzcorr/all_flights-*" tzcorr.json
