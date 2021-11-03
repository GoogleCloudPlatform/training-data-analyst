#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./ingest_from_crsbucket.sh  destination-bucket-name"
    exit
fi

BUCKET=$1
FROM=gs://data-science-on-gcp/flights/tzcorr
TO=gs://$BUCKET/flights/tzcorr

#sharded files
CMD="gsutil -m cp "
for SHARD in `seq -w 0 35`; do
  CMD="$CMD ${FROM}/all_flights-000${SHARD}-of-00036"
done
CMD="$CMD $TO"
echo $CMD
$CMD

# individual files
CMD="gsutil -m cp "
for FILE in airports/airports.csv.gz; do
   CMD="$CMD gs://data-science-on-gcp/flights/$FILE gs://$BUCKET/flights/$FILE"
done
echo $CMD
$CMD
