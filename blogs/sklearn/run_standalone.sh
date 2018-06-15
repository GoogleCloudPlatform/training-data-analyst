#!/bin/bash

#sudo pip install pandas-gbq=0.4.1 sklearn scipy

BUCKET=cloud-training-demos-ml
PROJECT=cloud-training-demos

export PYTHONPATH=${PYTHONPATH}:${PWD}/babyweight
python -m trainer.task \
   --bucket=${BUCKET} --frac=0.001 --job-dir=./tmp --projectId $PROJECT
