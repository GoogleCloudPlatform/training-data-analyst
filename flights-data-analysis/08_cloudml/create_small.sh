#!/bin/bash
mkdir -p ~/data/flights
gsutil cp gs://cloud-training-demos/flights/chapter07/flights-00000-of-00012.csv full.csv
head -10003 full.csv > ~/data/flights/small.csv
rm full.csv
