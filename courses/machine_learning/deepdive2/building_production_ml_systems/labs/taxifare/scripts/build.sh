#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

docker build $PROJECT_DIR -f $DOCKERFILE -t $IMAGE_URI
