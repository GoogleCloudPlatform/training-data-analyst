#!/bin/bash -e
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Run this command from one of the subdirectories. For example:
#     cd bqtocsv; ../build_container.sh


CONTAINER_NAME=babyweight-pipeline-$(basename $(pwd))
DIR_IN_REPO=$(pwd | sed 's%training-data-analyst/% %g' | awk '{print $2}')
REPO_DIR=$(pwd | sed 's%training-data-analyst/%training-data-analyst %g' | awk '{print $1}')

echo "Creating ${CONTAINER_NAME}:latest from this Dockerfile:"
cat ${REPO_DIR}/${DIR_IN_REPO}/Dockerfile


if [ -z "$1" ]; then
  PROJECT_ID=$(gcloud config config-helper --format "value(configuration.properties.core.project)")
else
  PROJECT_ID=$1
fi

if [ -z "$2" ]; then
  TAG_NAME="latest"
else
  TAG_NAME="$2"
fi

# Create the container image
cat <<EOM > cloudbuild.yaml
steps:
    - name: 'gcr.io/cloud-builders/docker'
      dir:  '${DIR_IN_REPO}'   # remove-for-manual
      args: [ 'build', '-t', 'gcr.io/${PROJECT_ID}/${CONTAINER_NAME}:${TAG_NAME}', '.' ]
images:
    - 'gcr.io/${PROJECT_ID}/${CONTAINER_NAME}:${TAG_NAME}'
EOM

# on the manual build, we should not specify dir:, but for github trigger, we need it
cat cloudbuild.yaml | grep -v "remove-for-manual" > /tmp/$$
cat /tmp/$$
gcloud builds submit . --config /tmp/$$

