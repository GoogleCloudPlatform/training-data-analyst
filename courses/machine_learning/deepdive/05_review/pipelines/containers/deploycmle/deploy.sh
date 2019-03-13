#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: ./deploy.sh  modeldir  modelname  modelversion"
    exit
fi

MODEL_LOCATION=$(gsutil ls $1/export/exporter | tail -1)
MODEL_NAME=$2
MODEL_VERSION=$3

TFVERSION=1.8
REGION=us-central1

# create the model if it doesn't already exist
modelname=$(gcloud ml-engine models list | grep -w "$MODEL_NAME")
echo $modelname
if [ -z "$modelname" ]; then
   echo "Creating model $MODEL_NAME"
   gcloud ml-engine models create ${MODEL_NAME} --regions $REGION
else
   echo "Model $MODEL_NAME already exists"
fi

# delete the model version if it already exists
modelver=$(gcloud ml-engine versions list --model "$MODEL_NAME" | grep -w "$MODEL_VERSION")
echo $modelver
if [ "$modelver" ]; then
   echo "Deleting version $MODEL_VERSION"
   yes | gcloud ml-engine versions delete ${MODEL_VERSION} --model ${MODEL_NAME}
   sleep 10
fi


echo "Creating version $MODEL_VERSION from $MODEL_LOCATION"
gcloud ml-engine versions create ${MODEL_VERSION} \
       --model ${MODEL_NAME} --origin ${MODEL_LOCATION} \
       --runtime-version $TFVERSION


echo $MODEL_NAME > /model.txt
echo $MODEL_VERSION > /version.txt
