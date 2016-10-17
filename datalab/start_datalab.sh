#!/bin/bash

IMAGE=gcr.io/cloud-datalab/datalab:local   # release

docker pull $IMAGE
docker run -t \
   -p "8081:8080" \
   -v "${HOME}:/content" \
   $IMAGE &
