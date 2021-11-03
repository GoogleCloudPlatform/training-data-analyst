#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./submit_spark.sh  bucket-name  pyspark-file"
    exit
fi

BUCKET=$1
PYSPARK=$2

gsutil -m rm -r gs://$BUCKET/flights/sparkmloutput
sed s"/BUCKET_NAME/$BUCKET/g" $2 > /tmp/logistic.py
gcloud dataproc jobs submit pyspark --cluster ch6cluster /tmp/logistic.py
