#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

docker push $IMAGE_URI
