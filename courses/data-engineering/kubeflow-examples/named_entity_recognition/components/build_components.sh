#!/bin/sh

echo "\nBuild and push preprocess component"
./preprocess/build_image.sh

echo "\nBuild and push train component"
./train/build_image.sh

echo "\nBuild and push deploy component"
./deploy/build_image.sh