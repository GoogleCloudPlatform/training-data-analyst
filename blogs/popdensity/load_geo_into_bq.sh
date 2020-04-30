#!/bin/bash

if test "$#" -ne 2; then
    echo "Usage: load_geo_into_bq.sh tablename staging-gcs-bucket"
    echo "   eg: load_geo_into_bq.sh popdensity ai-analytics-solutions-popdensity"
    exit
fi

TABLE=$1
BUCKET=$2


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
   advdata.${TABLE} $GCSFILE schema.json
