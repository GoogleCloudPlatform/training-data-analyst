#!/bin/bash
#
# A simple script for starting TFServing locally in a docker container.
# This allows us to test sending predictions to the model.
set -ex
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
MODELS_DIR="$( cd "${DIR}/../../t2t/test_data/" >/dev/null && pwd)"

MODEL_NAME=test_model_20181031

if [ ! -d ${MODELS_DIR}/${MODEL_NAME} ]; then
  echo Missing directory ${MODELS_DIR}/${MODEL_NAME}
  exit 1
fi

set +e
docker rm -f cs_serving_test
set -e

# TODO(jlewi): Is there anyway to cause TF Serving to load all models in
# MODELS_DIR and not have to specify the environment variable MODEL_NAME
docker run --rm --name=cs_serving_test -p 8500:8500 -p 8501:8501 \
   -v "${MODELS_DIR}:/models" \
   -e MODEL_NAME="${MODEL_NAME}" \
   tensorflow/serving
# Tail the logs
docker logs -f cs_serving_test
