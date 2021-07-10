#!/bin/bash -e

for container in $(ls -d */ | sed 's%/%%g'); do
  cd $container
  echo "Building Docker container in $container"
  bash ../build_container.sh
  cd ..
done
