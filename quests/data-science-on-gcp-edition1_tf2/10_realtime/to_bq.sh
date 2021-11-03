#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./to_bq.sh bucket-name"
    exit
fi

BUCKET=$1

bq load -F , flights2016.eval gs://$BUCKET/flights/chapter10/eval/*.csv evaldata.json
