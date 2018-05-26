#!/bin/bash

### This is a way to script out the creation of a key for your default
### Compute Service Account.  You can get your project number from the
### the GCP home page

KEYFILE=trainer/privatekey.json
PROJECTNUMBER=663413318684
if [ ! -f $KEYFILE ]; then
  gcloud iam service-accounts keys create \
      --iam-account ${PROJECTNUMBER}-compute@developer.gserviceaccount.com \
      $KEYFILE
fi
