#!/bin/#!/usr/bin/env bash
echo "Installing packages"
# Install modules
sh ./install_packages.sh

echo "Generating synthetic users"
# Generate 10 fake web site users
python3 user_generator.py --n=10

echo "Generating synthetic events"
python3 streaming_event_generator.py --project_id=$(gcloud config get-value project) -t=my_topic

