#!/bin/bash

#VMIP=`wget -qO - http://ipecho.net/plain`
#echo "Browse to http://$VMIP:8081/"

sudo docker run -t \
   -p "8081:8080" \
   -v "${HOME}:/content" \
   gcr.io/cloud-datalab/datalab:local &
