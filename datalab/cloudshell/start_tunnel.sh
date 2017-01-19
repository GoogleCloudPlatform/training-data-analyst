#!/bin/bash

echo "This command won't exit. click on the *Web Preview* (up-arrow button at top-left), select *port 8081*, and start using Datalab."

. ../instance_details.sh
echo "Tunneling to instance=$INSTANCE_NAME"

gcloud compute ssh --zone $ZONE \
   --ssh-flag="-N" --ssh-flag="-L" --ssh-flag="localhost:8081:localhost:8080" \
   ${USER}@$INSTANCE_NAME
