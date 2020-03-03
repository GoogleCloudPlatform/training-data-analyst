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
"""Creates a single project with specified service accounts and APIs enabled."""

import sys
from apis import ApiResourceName

def GenerateConfig(context): #pylint: disable=too-many-branches,too-many-statements
  """Generates config."""

  project_id = context.env['name']
  billing_name = 'billing_' + project_id

  if not IsProjectParentValid(context.properties):
    sys.exit(('Invalid [organization-id, parent-folder-id], '
              'must specify exactly one.'))

  parent_type = ''
  parent_id = ''

  if 'organization-id' in context.properties:
    parent_type = 'organization'
    parent_id = context.properties['organization-id']
  else:
    parent_type = 'folder'
    parent_id = context.properties['parent-folder-id']

  if 'project-name' in context.properties:
    project_name = context.properties['project-name']
  else:
    project_name = project_id

  resources = [{
      'name': project_id,
      'type': 'cloudresourcemanager.v1.project',
      'properties': {
          'name': project_name,
          'projectId': project_id,
          'parent': {
              'type': parent_type,
              'id': parent_id
          }
      }
  }, {
      'name': billing_name,
      'type': 'deploymentmanager.v2.virtual.projectBillingInfo',
      'metadata': {
          'dependsOn': [project_id]
      },
      'properties': {
          'name': 'projects/' + project_id,
          'billingAccountName': context.properties['billing-account-name']
      }
  }, {
      'name': 'apis',
      'type': 'apis.py',
      'properties': {
          'project': project_id,
          'billing': billing_name,
          'apis': context.properties['apis'],
          'concurrent_api_activation':
              context.properties['concurrent_api_activation']
      }
  }, {
      'name': 'service-accounts',
      'type': 'service-accounts.py',
      'properties': {
          'project': project_id,
          'service-accounts': context.properties['service-accounts']
      }
  }]
  if (context.properties.get('iam-policy-patch') or
      context.properties.get('set-dm-service-account-as-owner')):
    iam_policy_patch = context.properties.get('iam-policy-patch', {})
    if iam_policy_patch.get('add'):
      policies_to_add = iam_policy_patch['add']
    else:
      policies_to_add = []
    if iam_policy_patch.get('remove'):
      policies_to_remove = iam_policy_patch['remove']
    else:
      policies_to_remove = []

    if context.properties.get('set-dm-service-account-as-owner'):
      svc_acct = 'serviceAccount:{}@cloudservices.gserviceaccount.com'.format(
        '$(ref.{}.projectNumber)'.format(project_id)
      )

      # Merge the default DM service account into the owner role if it exists
      owner_idx = [bind['role'] == 'roles/owner' for bind in policies_to_add]
      try:
        # Determine where in policies_to_add the owner role is.
        idx = owner_idx.index(True)
      except ValueError:
        # If the owner role is not defined just append to what to add.
        policies_to_add.append({'role': 'roles/owner', 'members': [svc_acct]})
      else:
        # Append the default DM service account to the owner role members
        if svc_acct not in policies_to_add[idx]['members']:
          policies_to_add[idx]['members'].append(svc_acct)

    get_iam_policy_dependencies = [project_id]
    for api in context.properties['apis']:
      get_iam_policy_dependencies.append(ApiResourceName(project_id, api))

    resources.extend([{
        # Get the IAM policy first so that we do not remove any existing bindings.
        'name': 'get-iam-policy-' + project_id,
        'action': 'gcp-types/cloudresourcemanager-v1:cloudresourcemanager.projects.getIamPolicy',
        'properties': {
          'resource': project_id,
        },
        'metadata': {
          'dependsOn': get_iam_policy_dependencies,
          'runtimePolicy': ['UPDATE_ALWAYS']
        }
    }, {
        # Set the IAM policy patching the existing policy with what ever is currently in the
        # config.
        'name': 'patch-iam-policy-' + project_id,
        'action': 'gcp-types/cloudresourcemanager-v1:cloudresourcemanager.projects.setIamPolicy',
        'properties': {
          'resource': project_id,
          'policy': '$(ref.get-iam-policy-' + project_id + ')',
          'gcpIamPolicyPatch': {
             'add': policies_to_add,
             'remove': policies_to_remove
          }
        }
    }])
  if context.properties.get('bucket-export-settings'):
    bucket_name = None
    action_dependency = [project_id,
                         ApiResourceName(project_id, 'compute.googleapis.com')]
    if context.properties['bucket-export-settings'].get('create-bucket'):
      bucket_name = project_id + '-export-bucket'
      resources.append({
          'name': bucket_name,
          'type': 'gcp-types/storage-v1:buckets',
          'properties': {
              'project': project_id,
              'name': bucket_name
          },
          'metadata': {
              'dependsOn': [project_id,
                            ApiResourceName(
                                project_id, 'storage-component.googleapis.com')]
          }
      })
      action_dependency.append(bucket_name)
    else:
      bucket_name = context.properties['bucket-export-settings']['bucket-name']
    resources.append({
        'name': 'set-export-bucket',
        'action': 'gcp-types/compute-v1:compute.projects.setUsageExportBucket',
        'properties': {
            'project': project_id,
            'bucketName': 'gs://' + bucket_name
        },
        'metadata': {
            'dependsOn': action_dependency
        }
    })
  if context.properties.get('shared_vpc_host'):
    resources.append({
        'name': project_id + '-xpn-host',
        'type': 'compute.beta.xpnHost',
        'properties': {
            'organization-id': context.properties['organization-id'],
            'billing-account-name': context.properties['billing-account-name'],
            'project': project_id,
        },
        'metadata': {
            'dependsOn': [
                ApiResourceName(project_id, 'compute.googleapis.com'),
                project_id,
            ],
        }
     })
  if context.properties.get('shared_vpc_service_of'):
    resources.append({
        'name': project_id + '-xpn-service-' +
            context.properties['shared_vpc_service_of'],
        'type': 'compute.beta.xpnResource',
        'properties': {
            'organization-id': context.properties['organization-id'],
            'billing-account-name': context.properties['billing-account-name'],
            'project': [context.properties['shared_vpc_service_of']],
            'xpnResource': {
                'id': project_id,
                'type': 'PROJECT',
            },
        },
        'metadata': {
            'dependsOn': [
                ApiResourceName(project_id, 'compute.googleapis.com'),
                project_id,
                context.properties['shared_vpc_service_of'] + '-xpn-host',
            ],
        }
      })

  return {'resources': resources}

def IsProjectParentValid(properties):
  """ A helper function to validate that the project is either under a folder
      or under an organization and not both
  """
  if ('organization-id' not in properties and
      'parent-folder-id' not in properties):
    return False
  if 'organization-id' in properties and 'parent-folder-id' in properties:
    return False
  return True
