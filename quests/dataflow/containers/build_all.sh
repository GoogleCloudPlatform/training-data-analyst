#!/bin/bash -e

for container in $(ls -d */ | sed 's%/%%g'); do
  pushd $container
  echo "Building Docker container in $container"
  bash ./build_image.sh
  popd
done