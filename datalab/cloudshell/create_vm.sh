#!/bin/bash

. ../instance_details.sh
echo "Creating instance name=$INSTANCE_NAME in zone=$ZONE of type=$MACHINE_TYPE"

gcloud compute instances create $INSTANCE_NAME \
   --image-family=container-vm --image-project=google-containers \
   --zone $ZONE --machine-type $MACHINE_TYPE \
   --metadata "google-container-manifest=$(cat datalab.yaml)" \
   --scopes cloud-platform
