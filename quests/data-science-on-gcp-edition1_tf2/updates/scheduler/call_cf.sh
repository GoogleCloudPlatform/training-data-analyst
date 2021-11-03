#!/bin/bash

REGION='us-central1'
PROJECT=$(gcloud config get-value project)
BUCKET=cloud-training-demos-ml
URL=ingest_flights_udwaxx86mVygAmOazUcijW8zBXWNxEVM
TOKEN=changeme

echo {\"year\":\"2015\"\,\"month\":\"03\"\,\"bucket\":\"${BUCKET}\", \"token\":\"${TOKEN}\"} > /tmp/message
cat /tmp/message

curl -X POST "https://${REGION}-${PROJECT}.cloudfunctions.net/$URL" -H "Content-Type:application/json" --data-binary @/tmp/message

