#!/bin/bash

KEYFILE=babyweight/trainer/privatekey.json
PROJECTNUMBER=663413318684
if [ ! -f $KEYFILE ]; then
  gcloud iam service-accounts keys create \
      --iam-account ${PROJECTNUMBER}-compute@developer.gserviceaccount.com \
      $KEYFILE
fi
