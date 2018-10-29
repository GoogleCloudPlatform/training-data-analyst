#!/bin/bash
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

source util.sh

main() {
  # Get our working project, or exit if it's not set.
  local project_id=$(get_project_id)
  if [[ -z "$project_id" ]]; then
    exit 1
  fi
  local temp_file=$(mktemp)
  export TEMP_FILE="${temp_file}.yaml"
  mv "$temp_file" "$TEMP_FILE"

  # Because the included API is a template, we have to do some string
  # substitution before we can deploy it. Sed does this nicely.
  < "$API_FILE" sed -E "s/YOUR-PROJECT-ID/${project_id}/g" > "$TEMP_FILE"
  echo "Preparing config for deploying service in $API_FILE..."
  echo "To deploy:  gcloud endpoints services deploy $TEMP_FILE"
}

# Defaults.
API_FILE="../app/openapi.yaml"

if [[ "$#" == 0 ]]; then
  : # Use defaults.
elif [[ "$#" == 1 ]]; then
  API_FILE="$1"
else
  echo "Wrong number of arguments specified."
  echo "Usage: deploy_api.sh [api-file]"
  exit 1
fi

main "$@"
