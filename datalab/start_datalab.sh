#!/bin/bash

IMAGE=gcr.io/cloud-datalab/datalab:local   # release
#IMAGE=gcr.io/cloud-datalab/datalab:mlbeta2   # cloudml prebeta

export ENABLE_USAGE_REPORTING=false
sudo docker run -t \
   -p "8081:8080" \
   -v "${HOME}:/content" \
   $IMAGE &
