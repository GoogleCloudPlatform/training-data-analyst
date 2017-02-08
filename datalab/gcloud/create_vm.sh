#!/bin/bash

. ../instance_details.sh

echo "Creating instance=$INSTANCE_NAME in $ZONE"
echo "Wait for message that you can connect to localhost:8080"

datalab create --zone $ZONE $INSTANCE_NAME
