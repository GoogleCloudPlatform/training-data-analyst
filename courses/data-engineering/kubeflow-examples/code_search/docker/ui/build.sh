#!/usr/bin/env bash

##
# This script builds and pushes a Docker image containing
# the Code Search UI to Google Container Registry. It automatically tags
# a unique image for every run.
#
# Also note the PUBLIC_URL endpoint which can either be an FQDN or a path
# prefix to be used for the JS files in the React Application. It defaults
# to "/code-search" which means the search server will be accessible at
# https://PUBLIC_HOSTNAME/code-search.
#

set -ex

PROJECT=${PROJECT:-}
BUILD_IMAGE_UUID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:7]);')
BUILD_IMAGE_TAG="code-search-ui:v$(date +%Y%m%d)-${BUILD_IMAGE_UUID}"
PUBLIC_URL=${PUBLIC_URL:-"/code-search"}

if [[ ! -z "${PROJECT}" ]]; then
  BUILD_IMAGE_TAG="gcr.io/${PROJECT}/${BUILD_IMAGE_TAG}"
fi

# Directory of this script used for path references
_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd "${_SCRIPT_DIR}"

docker build -f "${_SCRIPT_DIR}/Dockerfile" \
             -t ${BUILD_IMAGE_TAG} \
             --build-arg PUBLIC_URL=${PUBLIC_URL} \
             "${_SCRIPT_DIR}/../.."

# Push images to GCR Project if available
if [[ ! -z "${PROJECT}" ]]; then
  docker push ${BUILD_IMAGE_TAG}
fi

popd
