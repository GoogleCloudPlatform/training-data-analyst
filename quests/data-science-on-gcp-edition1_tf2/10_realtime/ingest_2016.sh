#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./ingest_2016.sh bucket-name"
    exit
fi

export BUCKET=$1
export YEAR=2016

bash ../02_ingest/download.sh
bash ../02_ingest/zip_to_csv.sh
bash ../02_ingest/quotes_comma.sh
gsutil -m cp *.csv gs://$BUCKET/flights2016/raw
rm *.csv
