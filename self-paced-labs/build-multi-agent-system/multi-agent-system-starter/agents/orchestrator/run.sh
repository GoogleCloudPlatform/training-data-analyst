#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}"

if [[ "${SESSION_SERVICE_URI}" != "" ]]; then
    SESSION_SERVICE_PARAMETER="--session_service_uri ${SESSION_SERVICE_URI}"
elif [[ "${AGENT_ENGINE_ID}" != "" ]]; then
    SESSION_SERVICE_PARAMETER="--session_service_uri agentengine://${AGENT_ENGINE_ID}"
fi

if [[ "${MEMORY_SERVICE_URI}" != "" ]]; then
    MEMORY_SERVICE_PARAMETER="--memory_service_uri ${MEMORY_SERVICE_URI}"
elif [[ "${AGENT_ENGINE_ID}" != "" ]]; then
    MEMORY_SERVICE_PARAMETER="--memory_service_uri agentengine://${AGENT_ENGINE_ID}"
fi

if [[ "${ARTIFACT_SERVICE_URI}" != "" ]]; then
    ARTIFACT_SERVICE_PARAMETER="--artifact_service_uri ${ARTIFACT_SERVICE_URI}"
elif [[ "${ARTIFACTS_BUCKET}" != "" ]]; then
    ARTIFACT_SERVICE_PARAMETER="--artifact_service_uri gs://${ARTIFACTS_BUCKET}"
fi

if [[ "${PORT}" == "" ]]; then
    PORT="8080"
fi

if [[ "${ADDITIONAL_ADK_PARAMETERS}" != "" ]]; then
    echo "Additional parameters: ${ADDITIONAL_ADK_PARAMETERS}"
fi

python3 adk_app.py --host "0.0.0.0" --port ${PORT} \
    --trace_to_cloud \
    ${SESSION_SERVICE_PARAMETER} \
    ${MEMORY_SERVICE_PARAMETER} \
    ${ARTIFACT_SERVICE_PARAMETER} \
    ${ADDITIONAL_ADK_PARAMETERS} \
    .
