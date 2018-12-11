#!/bin/bash

if [ "$#" -lt 1 ]; then
   echo "Usage:   ./start_jupyter  user-google-account"
   exit
fi

MAIL=$1
INSTANCE_NAME=$(curl http://metadata.google.internal/computeMetadata/v1/instance/name -H "Metadata-Flavor: Google")
INSTANCE_ZONE="/"$(curl http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google")
INSTANCE_ZONE="${INSTANCE_ZONE##/*/}"

gcloud compute instances add-metadata "${INSTANCE_NAME}" \
	  --metadata proxy-user-mail="${MAIL}" --zone "${INSTANCE_ZONE}"

sudo /opt/deeplearning/bin/attempt-register-vm-on-proxy.sh

gcloud compute instances describe --zone "${INSTANCE_ZONE}" "${INSTANCE_NAME}" | grep datalab-vm | awk '{print "To access Jupyter, visit https://"$2}'
