#!/bin/bash
gsutil cp gs://cloud-training-demos-ml/flights/raw/201501.csv .
head -1000 201501.csv > 201501_part.csv
rm 201501.csv
