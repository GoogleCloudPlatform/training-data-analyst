#!/bin/bash

. ../instance_details.sh

echo "Deleting instance=$INSTANCE_NAME in $ZONE"

datalab delete --zone $ZONE $INSTANCE_NAME
