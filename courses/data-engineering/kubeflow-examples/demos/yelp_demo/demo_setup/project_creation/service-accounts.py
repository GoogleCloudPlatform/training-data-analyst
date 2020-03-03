# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Creates all service accounts for a specified project."""


def GenerateConfig(context):
  """Generates config."""

  project_id = context.properties['project']

  resources = []
  for service_account in context.properties['service-accounts']:
    resources.append({
        'name': project_id + '-' + service_account,
        'type': 'iam.v1.serviceAccount',
        'metadata': {
            'dependsOn': [project_id]
        },
        'properties': {
            'accountId': service_account,
            'displayName': service_account,
            'projectId': project_id
        }
    })

  return {'resources': resources}
