#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./create_cluster.sh  bucket-name  region"
    exit
fi

PROJECT=$(gcloud config get-value project)
BUCKET=$1
REGION=$2
INSTALL=gs://$BUCKET/flights/dataproc/install_on_cluster.sh

# upload install file
sed "s/CHANGE_TO_USER_NAME/$USER/g" install_on_cluster.sh > /tmp/install_on_cluster.sh
gsutil cp /tmp/install_on_cluster.sh $INSTALL

# create cluster
gcloud dataproc clusters create \
   --num-workers=2 \
   --scopes=cloud-platform \
   --worker-machine-type=n1-standard-4 \
   --master-machine-type=n1-standard-4 \
   --image-version=1.4 \
   --enable-component-gateway \
   --optional-components=ANACONDA,JUPYTER \
   --region=$REGION \
   --initialization-actions=$INSTALL \
   ch6cluster
