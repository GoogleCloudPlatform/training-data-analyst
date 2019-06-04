#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: ./run_notebook.sh  input_notebook output_gcs_dir  paramsfile"
    echo "   eg: ./run_notebook.sh  ../06_feateng_keras/taxifare_fc.ipynb  gs://cloud-training-demos-ml/quests/serverlessml/notebook notebook_params.yaml"
    exit
fi

set -x

INSTANCE_NAME=notebook$(date +%Y%m%d%H%M%S)
INPUT_NOTEBOOK=$1
GCS_OUTPUT_DIR=$2/${INSTANCE_NAME}
INPUT_PARAMS=$3

# gcloud compute images list --project deeplearning-platform-release --no-standard-images
export IMAGE_FAMILY="tf-2-0-cu100-experimental"
export ZONE="us-west1-b"
export INSTANCE_TYPE="n1-standard-4"

# copy the inputs to GCS
gsutil cp $INPUT_NOTEBOOK $INPUT_PARAMS $GCS_OUTPUT_DIR/inputs || exit 1
export GCS_INPUT_NOTEBOOK="$GCS_OUTPUT_DIR/inputs/$(basename $INPUT_NOTEBOOK)"
export GCS_INPUT_PARAMS="$GCS_OUTPUT_DIR/inputs/$(basename $INPUT_PARAMS)"
export GCS_OUTPUT_NOTEBOOK="$GCS_OUTPUT_DIR/$(basename $INPUT_NOTEBOOK)"
export LAUNCHER_SCRIPT="papermill ${GCS_INPUT_NOTEBOOK} ${GCS_OUTPUT_NOTEBOOK} -y ${GCS_INPUT_PARAMS}"

gcloud compute instances create $INSTANCE_NAME \
        --zone=$ZONE \
        --image-family=$IMAGE_FAMILY \
        --image-project=deeplearning-platform-release \
        --maintenance-policy=TERMINATE \
        --accelerator='type=nvidia-tesla-p100,count=1' \
        --machine-type=$INSTANCE_TYPE \
        --boot-disk-size=200GB \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --metadata="install-nvidia-driver=True,startup-script=$LAUNCHER_SCRIPT" || exit 1

echo "Please monitor the VM on the GCP console; once the VM exits, the output notebook should be available in $GCS_OUTPUT_NOTEBOOK"