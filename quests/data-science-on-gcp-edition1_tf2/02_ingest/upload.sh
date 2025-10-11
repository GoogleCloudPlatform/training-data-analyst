#!/bin/bash
export BUCKET=${BUCKET:=cloud-training-demos-ml}
echo "Uploading to bucket $BUCKET..."
gcloud storage cp *.csv gs://$BUCKET/flights/raw
# TODO: The permission shorthand "R" in "gsutil acl ch -g google.com:R" is not defined in the migration guide. Manual review required.
#gsutil -m acl ch -R -g google.com:R gs://$BUCKET/flights/raw
