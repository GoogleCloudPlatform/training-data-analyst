#!/bin/bash

# CHANGE
BUCKET="ai-analytics-solutions-kfpdemo"

# test cloud function
echo "Creating new file in gs://${BUCKET}"
gsutil cp gs://${BUCKET}/babyweight/preproc/train_2000.csv-00002-* \
          gs://${BUCKET}/babyweight/preproc/train_20200207.csv


