#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: ./run_notebook.sh  input_notebook output_notebook output_gcs_dir paramsfile"
    echo "   eg: ./run_notebook.sh  ../06_feateng_keras/taxifare_fc.ipynb ./feat_eng_full.ipynb gs://cloud-training-demos-ml/quests/serverlessml/notebook notebook_params.yaml"
    exit
fi

#set -x

INSTANCE_NAME=notebook$(date +%Y%m%d%H%M%S)
INPUT_NOTEBOOK=$1
OUTPUT_NOTEBOOK=$2
GCS_OUTPUT_DIR=$3/${INSTANCE_NAME}
INPUT_PARAMS=$4

# gcloud compute images list --project deeplearning-platform-release --no-standard-images
export IMAGE_FAMILY="tf-2-0-cu100-experimental"
export ZONE="us-west1-b"
export INSTANCE_TYPE="n1-standard-4"

# copy the inputs to GCS
gsutil cp $INPUT_NOTEBOOK $INPUT_PARAMS $GCS_OUTPUT_DIR/inputs || exit 1
export GCS_INPUT_NOTEBOOK="$GCS_OUTPUT_DIR/inputs/$(basename $INPUT_NOTEBOOK)"
export GCS_INPUT_PARAMS="$GCS_OUTPUT_DIR/inputs/$(basename $INPUT_PARAMS)"
export GCS_OUTPUT_NOTEBOOK="$GCS_OUTPUT_DIR/$(basename $INPUT_NOTEBOOK)"
export LAUNCHER_SCRIPT="https://raw.githubusercontent.com/GoogleCloudPlatform/ml-on-gcp/master/dlvm/tools/scripts/notebook_executor.sh"
#export LAUNCHER_SCRIPT="https://raw.githubusercontent.com/GoogleCloudPlatform/ml-on-gcp/7311f1e270f5e896e01a522c46e17fc230cf8f84/dlvm/tools/scripts/notebook_executor.sh"

echo "Please monitor the VM on the GCP console"
echo "Once the VM is ready (while it is running), you can monitor the logs using:"
echo "     gcloud compute instances get-serial-port-output --zone $ZONE $INSTANCE_NAME"
echo "Once the VM exits, the output notebook will be in $GCS_OUTPUT_NOTEBOOK"

gcloud compute instances create $INSTANCE_NAME \
        --zone=$ZONE \
        --image-family=$IMAGE_FAMILY \
        --image-project=deeplearning-platform-release \
        --maintenance-policy=TERMINATE \
        --accelerator='type=nvidia-tesla-p100,count=1' \
        --machine-type=$INSTANCE_TYPE \
        --boot-disk-size=200GB \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --metadata="input_notebook_path=${GCS_INPUT_NOTEBOOK},output_notebook_path=${GCS_OUTPUT_NOTEBOOK},parameters_file=${GCS_INPUT_PARAMS},startup-script-url=$LAUNCHER_SCRIPT" || exit 1

# copy locally
echo "if you ctrl-C this, you will have to manually copy over the file"
echo "gsutil cp ${GCS_OUTPUT_NOTEBOOK}  $OUTPUT_NOTEBOOK"

while true; do
   proxy=$(gcloud compute instances describe --zone $ZONE $INSTANCE_NAME --format="value(status)"  2> /dev/null | grep -v RUNNING)
   if [ -z "$proxy" ]
   then
      echo -n "."
      sleep 1
   else
      echo "done!"
      break
   fi
done

gsutil cp ${GCS_OUTPUT_NOTEBOOK} ${OUTPUT_NOTEBOOK} || exit 1
