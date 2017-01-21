#!/bin/bash

. ../instance_details.sh

echo "Tunneling to instance=$INSTANCE_NAME in $ZONE"

datalab connect --zone $ZONE $INSTANCE_NAME
