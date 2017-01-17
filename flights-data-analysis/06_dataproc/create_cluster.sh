#!/bin/bash

BUCKET=cloud-training-demos-ml
ZONE=us-central1-a
INSTALL=gs://$BUCKET/flights/dataproc/install_on_cluster.sh

# upload install file
gsutil cp install_on_cluster.sh $INSTALL

# create cluster
gcloud dataproc clusters create \
   --bucket=$BUCKET \
   --num-workers=2 \
   --scopes=cloud-platform \
   --worker-machine-type=n1-standard-2 \
   --master-machine-type=n1-standard-4 \
   --zone=$ZONE \
   --initialization-actions=gs://dataproc-initialization-actions/datalab/datalab.sh,$INSTALL \
   ch6cluster
