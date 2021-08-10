#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

docker run --rm \
  -v "${HOME}/.config/gcloud":/root/.config/gcloud \
  $IMAGE_URI "$@"
