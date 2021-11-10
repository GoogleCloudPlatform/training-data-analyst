#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage:        ./deploy_model.sh bucket best_model region"
    echo "  Note the slash after the number of the best model if you did hyperparam:"
    echo "   eg:        ./deploy_model.sh cloud-training-demos-ml 15/ us-central1"
    echo "  Supply an empty string for the best_model if you did not do hyperparam:"
    echo "   eg:        ./deploy_model.sh cloud-training-demos-ml ''  us-central1"
    exit
fi

BUCKET=$1
PROJECT=$(gcloud config get-value project)
BEST_MODEL=$2   # use an empty string if you didn't do hyperparam tuning
REGION=$3

MODEL_NAME=flights
VERSION_NAME=tf2
EXPORT_PATH=$(gsutil ls gs://$BUCKET/flights/trained_model/${BEST_MODEL}export | tail -1)
echo $EXPORT_PATH

if [[ $(gcloud ai-platform models list --format='value(name)' --region=$REGION | grep $MODEL_NAME) ]]; then
    echo "$MODEL_NAME already exists"
else
    # create model
    echo "Creating $MODEL_NAME"
    gcloud ai-platform models create --region=$REGION $MODEL_NAME
fi

if [[ $(gcloud ai-platform versions list --model $MODEL_NAME --format='value(name)' --region=$REGION | grep $VERSION_NAME) ]]; then
    echo "Deleting already existing $MODEL_NAME:$VERSION_NAME ... "
    gcloud ai-platform versions delete --quiet --region=$REGION --model=$MODEL_NAME $VERSION_NAME
    echo "Please run this cell again if you don't see a Creating message ... "
    sleep 10
fi

# create model
echo "Creating $MODEL_NAME:$VERSION_NAME"
gcloud ai-platform versions create --model=$MODEL_NAME $VERSION_NAME --async \
       --framework=tensorflow --python-version=3.7 --runtime-version=2.3 \
       --origin=$EXPORT_PATH --staging-bucket=gs://$BUCKET --region=$REGION
