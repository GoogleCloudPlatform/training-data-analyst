#!/bin/bash

IMAGE=gcr.io/cloud-datalab/datalab:local   # release

# optionally, add a line like this to the docker run command:
# (change your project-id to match)
# if you don't do this, datalab will ask you to sign in and
# set a project-id
#   -e "PROJECT_ID=cloud-training-demos" \

docker pull $IMAGE
docker run -t \
   -p "8081:8080" \
   -v "${HOME}:/content" \
   $IMAGE &
