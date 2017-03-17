#!/bin/bash

# If the PROJECT_ID environment variable is not set, Datalab will ask you
# to set a project id when you try to use GCP resources such as BigQuery.
# PROJECT_ID='your-project-id'
IMAGE=gcr.io/cloud-datalab/datalab:latest   # release

# By default, the home directory is used to store Cloud Datalab notebooks and
# configurations. If you want to change this directory, simply update the
# CONTENT variable below to the desired directory, or set the environment
# variable before launching this script
if [ -z $CONTENT ]; then
   CONTENT=${HOME}
   echo "Defaulting to $CONTENT to store your notebooks"
else
   echo "Using $CONTENT to store your notebooks based on env variable"
fi

if [ ! -d $CONTENT ]; then
    echo "CONTENT directory does not exist. Please check start_datalab.sh"
    exit 1
fi

cd $CONTENT
if [ ! -d "training-data-analyst" ]; then
   git clone http://github.com/GoogleCloudPlatform/training-data-analyst/
fi

# On linux, docker runs directly on the host machine. It's important to bind to
# 127.0.0.1 only to ensure that Datalab is not accessible on your local network.
# On other platforms, bind to all ip addresses so VirtualBox can access it.
# Users need to make sure that their VirtualBox port forwarding setting only
# binds to 127.0.0.1.
if [ "$OSTYPE" == "linux"* ]; then
  PORTMAP="127.0.0.1:8081:8080"
else
  PORTMAP="8081:8080"
fi

docker pull $IMAGE
docker run -it \
   -p $PORTMAP \
   -v "$CONTENT:/content" \
   -e "PROJECT_ID=$PROJECT_ID" \
   $IMAGE
