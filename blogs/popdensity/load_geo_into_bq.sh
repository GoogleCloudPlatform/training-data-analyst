#!/bin/bash

BUCKET=cloud-training-demos-ml   # change as needed

FILE=popdensity_geo.json.gz
GCSFILE=gs://$BUCKET/popdensity/$FILE

gsutil -m cp $FILE $GCSFILE

bq_safe_mk() {
    dataset=$1
    exists=$(bq ls -d | grep -w $dataset)
    if [ -n "$exists" ]; then
       echo "Not creating $dataset since it already exists"
    else
       echo "Creating $dataset"
       bq mk $dataset
    fi
}

bq_safe_mk advdata
bq load --replace \
   --source_format NEWLINE_DELIMITED_JSON \
   --range_partitioning=year,1900,2100,5 \
   --clustering_fields tile \
   advdata.popdensity $GCSFILE schema.json
