#!/bin/bash
BUCKET=cloud-training-demos-ml  # CHANGE

gsutil cp *.ipynb gs://$BUCKET/notebooks/jupyter
