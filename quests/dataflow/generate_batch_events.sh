#!/bin/#!/usr/bin/env bash
echo "Installing packages"
# Install modules
sh ./install_packages.sh

echo "Generating synthetic users"
# Generate 2 fake web site users
python3 user_generator.py --n=2

echo "Generating synthetic events"
rm *.out
# Generate 10 events
python3 event_generator.py -x=taxonomy.json --num_e=10 --project_id=$(gcloud config get-value project)
cat *.out >> events.json
rm *.out

echo "Copying events to Cloud Storage"
# Set BUCKET to the non-coldline Google Cloud Storage bucket
export BUCKET=$(gsutil ls)
# Copy events.json into the bucket
gsutil cp events.json ${BUCKET}
