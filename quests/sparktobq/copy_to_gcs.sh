#!/bin/bash
BUCKET=cloud-training-demos-ml  # CHANGE

gcloud storage cp *.ipynb gs://$BUCKET/notebooks/jupyter
