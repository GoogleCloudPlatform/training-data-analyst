#!/bin/bash

# Go to the standard location
cd ~/training-data-analyst/courses/unstructured/

# "If at first you don't succeed, try, try again."
#   If this is our first time here, backup the program files
#   If this is a subsequent run, restore fresh from backup before proceeding
#
if [ -d "backup" ]; then
  cp backup/*dataproc* .
else
  mkdir backup
  cp *dataproc* backup
fi

# Verify that the environment variables exist
#
OKFLAG=1
if [[ -v $BUCKET ]]; then
  echo "BUCKET environment variable not found"
  OKFLAG=0
fi
if [[ -v $DEVSHELL_PROJECT_ID ]]; then
  echo "DEVSHELL_PROJECT_ID environment variable not found"
  OKFLAG=0
fi
if [[ -v $APIKEY ]]; then
  echo "APIKEY environment variable not found"
  OKFLAG=0
fi


if [ OKFLAG==1 ]; then
  # Edit the script files
  sed -i "s/your-api-key/$APIKEY/" *dataprocML.py
  sed -i "s/your-project-id/$DEVSHELL_PROJECT_ID/" *dataprocML.py
  sed -i "s/your-bucket/$BUCKET/" *dataprocML.py

  # Copy python scripts to the bucket
  gsutil cp *dataprocML.py gs://$BUCKET/

  # Copy data to the bucket
  gsutil cp gs:\/\/cloud-training\/gcpdei\/road* gs:\/\/$BUCKET\/sampledata\/ 
  gsutil cp gs:\/\/cloud-training\/gcpdei\/time* gs:\/\/$BUCKET\/sampledata\/

fi




