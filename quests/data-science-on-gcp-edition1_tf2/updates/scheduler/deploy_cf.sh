#!/bin/bash

URL=ingest_flights_$(openssl rand -base64 48 | tr -d /=+ | cut -c -32)
echo $URL

gcloud functions deploy $URL --runtime python37 --trigger-http --timeout 480s
