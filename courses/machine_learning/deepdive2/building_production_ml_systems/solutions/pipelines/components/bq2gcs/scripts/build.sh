#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

docker build $COMPONENT_DIR -f $DOCKERFILE -t $IMAGE_URI
