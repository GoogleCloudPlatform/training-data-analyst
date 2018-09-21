#!/bin/bash

BUCKET=cloud-training-demos-ml
./csv_to_infapi.py --input gs://cloud-training-demos/flights/tzcorr/all_flights* --output_prefix gs://${BUCKET}/flights/json/flights_data --runner DataflowRunner --project $(gcloud config get-value project) --staging_location gs://${BUCKET}/temp --temp_location gs://${BUCKET}/temp
