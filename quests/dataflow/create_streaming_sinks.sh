#!/bin/#!/usr/bin/env bash
echo "Creating pipeline sinks"

PROJECT_ID=$(gcloud config get-value project)

# GCS buckets
#TODO: Add try/catch for the first bucket since qwiklabs
gcloud storage buckets create --location=US gs://$PROJECT_ID
gcloud storage buckets create --location=US --default-storage-class="COLDLINE" gs://$PROJECT_ID-coldline

# BiqQuery Dataset
bq mk --location=US logs

# PubSub Topic
gcloud pubsub topics create my_topic