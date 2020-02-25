#! /bin/bash

# Clone the Data Analyst Repo
#
# Git may not be installed by default or might be dated
#  Need JDK
#  Need Maven
#
  apt-get update
  apt-get install git -y
  apt-get install default-jdk -y
  apt-get install maven -y

# Install software for SDP
  apt-get install -y python-pip
  pip install -U google-cloud-pubsub

# User does not exist on the VM at boot time so this is in folder /training at root
# User can copy to home using:  cp -r /training  .
  mkdir training
  cd training
  git clone https://github.com/GoogleCloudPlatform/training-data-analyst

  source /training/training-data-analyst/courses/streaming/env_scripts/project_env.sh
  chmod +x /training/training-data-analyst/courses/streaming/env_scripts/sensor_magic.sh
  chmod +x /training/training-data-analyst/courses/streaming/env_scripts/project_env.sh
# gsutil cp gs://cloud-training/gcpdei/road-not-taken.txt .
# gsutil cp gs://cloud-training/gcpdei/sherlock-holmes.txt .

# Example of enabling a GCP API
#
#   Enable the DataFlow API
  gcloud services enable dataflow.googleapis.com


# Example of installing software
#
# Install Apache Beam for Python
#  apt-get install python-pip -y
#  pip install google-cloud-dataflow oauth2client==3.0.0
#  pip install --force six==1.10  # downgrade as 1.11 breaks apitools
#  pip install -U pip
#  pip -V
#
