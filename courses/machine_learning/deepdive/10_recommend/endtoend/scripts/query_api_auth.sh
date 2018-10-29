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
  # Because our included app uses query string parameters, we can include
  # them directly in the URL. We use -H to specify a header with our API key.
  QUERY="curl -H 'x-api-key: $API_KEY' \"https://${project_id}.appspot.com/recommendation?userId=${USER_ID}\""
  # First, print the command so the user can see what's being executed.
  echo "$QUERY"
  # Then actually execute it.
  # shellcheck disable=SC2086
  eval $QUERY
  # Our API doesn't print newlines. So we do it ourselves.
  printf '\n'
}

# Defaults.
USER_ID="5448543647176335931"

if [[ "$#" == 1 ]]; then
  API_KEY="$1"
elif [[ "$#" == 2 ]]; then
  # "Quiet mode" won't print the curl command.
  API_KEY="$1"
  USER_ID="$2"
else
  echo "Wrong number of arguments specified."
  echo "Usage: query_api_auth.sh api-key [user-id]"
  exit 1
fi

main "$@"
