#!/bin/bash

BUCKET=cloud-training-demos-ml

gcloud dataproc clusters create my-cluster --zone us-central1-a \
	--master-machine-type n1-standard-1 --master-boot-disk-size 50 \
	--num-workers 2 --worker-machine-type n1-standard-1 \
	--worker-boot-disk-size 50 --network=default \
        --initialization-actions=gs://$BUCKET/unstructured/init-script.sh,gs://dataproc-initialization-actions/datalab/datalab.sh

