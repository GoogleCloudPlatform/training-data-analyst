#!/bin/bash
gsutil cat gs://cloud-training-demos-ml/flights/raw/201501.csv | head -1000 > 201501_part.csv
