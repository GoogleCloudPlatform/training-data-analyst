#!/bin/bash
# TODO(ankushagarwal): Convert this to a python launcher script
set -x
echo environment
env | sort
WORKER_ID=$(echo ${TF_CONFIG} | jq ".task.index")
WORKER_TYPE=$(echo ${TF_CONFIG} | jq -r ".task.type")
MASTER_INSTANCE=$(echo ${TF_CONFIG} | jq -r ".cluster.${WORKER_TYPE}[${WORKER_ID}]")
t2t-trainer \
  --master=grpc://${MASTER_INSTANCE} \
  --worker_id=${WORKER_ID} \
  --tmp_dir=/tmp \
  "$@"
