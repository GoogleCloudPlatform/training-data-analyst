#! /bin/bash

# Clone the Data Analyst Repo
#
# Git may not be installed by default or might be dated
# 
  apt-get update
  apt-get install git -y

# User does not exist on the VM at boot time so this is in folder /training at root
# User can copy to home using:  cp -r /training  .
  mkdir training
  cd training
  git clone https://github.com/GoogleCloudPlatform/training-data-analyst

# Example of copying sample data files from a bucket
#
# gsutil cp gs://cloud-training/gcpdei/road-not-taken.txt .
# gsutil cp gs://cloud-training/gcpdei/sherlock-holmes.txt .

# Example of enabling a GCP API
#
#   Enable the DataFlow API
#  gcloud services enable dataflow.googleapis.com 

# Example of installing software
#
# Install Apache Beam for Python
#  apt-get install python-pip -y
#  pip install google-cloud-dataflow oauth2client==3.0.0 
#  pip install --force six==1.10  # downgrade as 1.11 breaks apitools
#  pip install -U pip
#  pip -V
#
