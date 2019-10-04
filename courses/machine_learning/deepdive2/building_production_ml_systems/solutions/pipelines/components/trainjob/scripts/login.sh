#!/bin/bash

source "$(cd $(dirname $BASH_SOURCE) && pwd)/env.sh"

docker run -it --rm \
  --entrypoint=/bin/bash \
  -w /code \
  -v $COMPONENT_DIR:/code \
  -v "${HOME}/.config/gcloud":/root/.config/gcloud \
  $IMAGE_URI
