#!/bin/#!/usr/bin/env bash
echo "Creating pipeline sinks"

PROJECT_ID=$(gcloud config get-value project)

# GCS buckets
#TODO: Add try/catch for the first bucket since qwiklabs
gcloud storage buckets create gs://$PROJECT_ID --location=US
gcloud storage buckets create gs://$PROJECT_ID-coldline --location=US --default-storage-class="COLDLINE"

# BiqQuery Dataset
bq mk --location=US logs