#!/bin/bash

gcloud dataproc jobs submit pyspark \
       --cluster sparktobq \
       spark_analysis.py \
       -- --bucket=cloud-training-demos-ml