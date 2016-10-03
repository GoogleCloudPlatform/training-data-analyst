#!/bin/bash

echo "This command won't exit. click on the *Web Preview* (up-arrow button at top-left), select *port 8081*, and start using Datalab."

# Remove "_" from USER because "_" can not be used for instance name
INSTANCE_NAME=${USER//_/}

# if you change the zone from us-central1-a in ./create_vm.sh, change it here too
gcloud compute ssh --zone us-central1-a \
   --ssh-flag="-N" --ssh-flag="-L" --ssh-flag="localhost:8081:localhost:8080" \
   ${USER}@datalabvm-${INSTANCE_NAME}
