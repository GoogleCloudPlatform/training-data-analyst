#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage ./create_vm.sh browser-ip-address"
    echo "           You can get the IP address presented by your browser by browsing to http://ip4.me/"
    exit
fi

# create a firewall rule that allows 8081 access
BROWSER_IP=$1
echo "Creating firewall rule that allows http access on 8081 from $BROWSER_IP"
gcloud compute firewall-rules create datalab8081 \
   --allow tcp:8081 --description "Allow connection to datalab" \
   --source-ranges $BROWSER_IP --target-tags datalab8081

# create VM with the tag corresponding to above firewall rule
gcloud compute instances create datalabvm \
   --image-family=container-vm --image-project=google-containers \
   --zone us-central1-a --machine-type n1-standard-1 \
   --tags datalab8081 \
   --scopes cloud-platform
