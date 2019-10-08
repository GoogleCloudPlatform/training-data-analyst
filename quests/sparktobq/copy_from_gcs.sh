#!/bin/bash
BUCKET=cloud-training-demos-ml  # CHANGE

gsutil cp gs://$BUCKET/notebooks/jupyter/* .
