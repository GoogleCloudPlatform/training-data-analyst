#!/bin/bash

for build_file in $(ls */build.sh); do
  echo $build_file
  cd $(dirname $build_file)
  bash ./build.sh
  cd ..
done
