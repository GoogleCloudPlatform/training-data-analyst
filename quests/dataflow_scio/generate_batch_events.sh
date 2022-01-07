#!/bin/#!/usr/bin/env bash
echo "Installing packages"
# Install modules
sh ./install_packages.sh

echo "Generating synthetic users"
# Generate 2 fake web site users
python3 user_generator.py --n=10

echo "Generating synthetic events"
rm *.out 2> /dev/null
# Generate 10 events
python3 batch_event_generator.py --num_e=1000

echo "Copying events to Cloud Storage"
# Set BUCKET to the non-coldline Google Cloud Storage bucket
export BUCKET=gs://$(gcloud config get-value project)/
# Copy events.json into the bucket
gsutil cp events.json ${BUCKET}
