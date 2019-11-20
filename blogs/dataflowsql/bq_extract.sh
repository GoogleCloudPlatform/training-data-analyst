#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./bq_export.sh  bucket-name"
    exit
fi

BUCKET=$1

PROJECT=$(gcloud config get-value project)

bq --project=$PROJECT extract --destination_format=NEWLINE_DELIMITED_JSON \
   bigquery-public-data:ncaa_basketball.mbb_historical_tournament_games \
   gs://$BUCKET/ncaa/mbb_historical_tournament_games.json

bq --project=$PROJECT extract --destination_format=AVRO \
   bigquery-public-data:ncaa_basketball.mbb_historical_tournament_games \
   gs://$BUCKET/ncaa/mbb_historical_tournament_games.avro
