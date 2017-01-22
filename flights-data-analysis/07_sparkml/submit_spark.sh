#!/bin/bash
gsutil -m rm -r gs://cloud-training-demos-ml/flights/sparkmloutput
gcloud dataproc jobs submit pyspark --cluster ch6cluster $*
