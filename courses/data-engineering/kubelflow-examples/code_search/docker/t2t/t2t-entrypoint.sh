#!/usr/bin/env bash
# This script is a wrapper script for T2T.
# T2T relies on various command line variables to be set in addition to TFCONFIG being set..
# So this script parses TF_CONFIG and then appends appropriate command line arguments
# to whatever command was entered.
set -ex
echo environment
env | sort
WORKER_ID=$(echo ${TF_CONFIG} | jq ".task.index")
WORKER_TYPE=$(echo ${TF_CONFIG} | jq -r ".task.type")
MASTER_INSTANCE=$(echo ${TF_CONFIG} | jq -r ".cluster.${WORKER_TYPE}[${WORKER_ID}]")
"$@" \
  --master=grpc://${MASTER_INSTANCE} \
  --worker_id=${WORKER_ID} \

# Sleep to give fluentd time to capture logs
sleep 120
