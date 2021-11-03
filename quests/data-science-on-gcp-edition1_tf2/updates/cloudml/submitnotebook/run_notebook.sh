#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: ./deploy.sh  input_notebook output_notebook paramsfile"
    exit
fi

IN_NB_GCS=$1
OUT_NB_GCS=$2
PARAMS_GCS=$3

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

mkdir working
cd working
gsutil cp $IN_NB_GCS  input.ipynb
gsutil cp $PARAMS_GCS params.yaml
papermill input.ipynb output.ipynb -f params.yaml --log-output
gsutil cp output.ipynb $OUT_NB_GCS
cd ..
rm -rf working

