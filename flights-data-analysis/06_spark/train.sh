#!/bin/bash
gsutil rm -r gs://cloud-training-demos/flights/sparkoutput
gcloud beta dataproc jobs submit pyspark --cluster cluster-1 logistic.py
