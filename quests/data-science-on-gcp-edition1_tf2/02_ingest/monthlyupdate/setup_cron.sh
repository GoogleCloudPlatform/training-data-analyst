#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: ./setup_cron.sh  destination-bucket-name compute-region ingest-url  personal-access-token"
    echo "   eg: ./setup_cron.sh  cloud-training-demos-ml us-central1 ingest_flights_udwaxx86mVygAmOazUcijW8zBXWNxEVM  DI8TWPzTedNF0b3B8meFPxXSWw6m3bKG"
    exit
fi

PROJECT=$(gcloud config get-value project)
BUCKET=$1
REGION=$2
UPATH=$3
TOKEN=$4

URL="https://${REGION}-${PROJECT}.cloudfunctions.net/${UPATH}"
echo {\"bucket\":\"${BUCKET}\"\,\"token\":\"${TOKEN}\"} > /tmp/message

gcloud beta scheduler jobs create http monthlyupdate \
       --schedule="8 of month 10:00" \
       --uri=$URL \
       --max-backoff=7d \
       --max-retry-attempts=5 \
       --max-retry-duration=3h \
       --min-backoff=1h \
       --time-zone="US/Eastern" \
       --message-body-from-file=/tmp/message
