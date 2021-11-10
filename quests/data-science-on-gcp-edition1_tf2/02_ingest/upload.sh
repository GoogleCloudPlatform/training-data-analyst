#!/bin/bash
export BUCKET=${BUCKET:=cloud-training-demos-ml}
echo "Uploading to bucket $BUCKET..."
gsutil -m cp *.csv gs://$BUCKET/flights/raw
#gsutil -m acl ch -R -g google.com:R gs://$BUCKET/flights/raw
