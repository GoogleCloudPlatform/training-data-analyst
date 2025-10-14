#!/bin/bash
BUCKET=cloud-training-demos-ml  # CHANGE

gcloud storage cp gs://$BUCKET/notebooks/jupyter/* .
