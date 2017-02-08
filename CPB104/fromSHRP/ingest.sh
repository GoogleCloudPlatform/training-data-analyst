#!/bin/bash

# curl http://shrp2archive.org/?attachment_id=896# -O SD_5min.csv
gsutil cp gs://hsd_freeway_data/SD_5min.csv raw.csv
python to_messages.py > messages.csv
gsutil cp messages.csv gs://cloud-training-demos/sandiego/sensor_obs.csv
