#!/bin/bash

gcloud storage cp gs://sd_freeway_data/SD_5min.csv raw.csv
python to_messages.py
gcloud storage cp messages.csv.gz gs://cloud-training-demos/sandiego/sensor_obs2008.csv.gz
