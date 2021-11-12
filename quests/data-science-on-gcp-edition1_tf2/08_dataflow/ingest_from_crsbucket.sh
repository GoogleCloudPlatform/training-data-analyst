#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./ingest_from_crsbucket.sh  destination-bucket-name"
    exit
fi

BUCKET=$1
FROM=gs://data-science-on-gcp/flights/chapter8/output
TO=gs://$BUCKET/flights/chapter8/output

CMD="gsutil -m cp "
for SHARD in `seq -w 0 6`; do
  CMD="$CMD ${FROM}/testFlights-0000${SHARD}-of-00007.csv"
done
for SHARD in `seq -w 0 6`; do
  CMD="$CMD ${FROM}/trainFlights-0000${SHARD}-of-00007.csv"
done
CMD="$CMD ${FROM}/delays.csv $TO"

echo $CMD
$CMD
