#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./tobq.sh  bucket-name"
    exit
fi

BUCKET=$1


bq load -F , flights.trainFlights gs://$BUCKET/flights/chapter8/output/trainFlights* mldataset.json
bq load -F , flights.testFlights gs://$BUCKET/flights/chapter8/output/testFlights* mldataset.json
