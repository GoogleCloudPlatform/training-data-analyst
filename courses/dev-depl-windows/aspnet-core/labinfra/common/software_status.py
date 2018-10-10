# Copyright 2016 Google Inc. All rights reserved.
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
"""A DM template that generates software status resources and outputs.

An example YAML showing how this template can be used:
  resources:
  - name: software-status
    type: software_status.py
    properties:
      timeout: 300
      waiterDependsOn:
        - wordpress-vm
  - name: software-status-script
    type: software_status_script.py
    properties:
      checkType: bitnami
  - name: wordpress-vm
    type: vm_instance.py
    properties:
      instanceName: wordpress-vm
      serviceAccounts:
        - scopes:
            - 'https://www.googleapis.com/auth/cloudruntimeconfig'
      metadata:
        items:
          - key: status-config
            value: $(ref.software-status.config)
          - key: status-endpoint
            value: $(ref.software-status.endpoint)
          - key: status-path
            value: $(ref.software-status.path)
          - key: startup-script
            value: $(ref.software-status-script.startup-script)

  Input properties to this template:
  - timeout: optional. The time to wait for startup success. 5 minute default.
  - waiterDependsOn: optional. A list of waiter dependency names (e.g., VMs).
"""
import types
import yaml

RTC_ENDPOINT = 'https://runtimeconfig.googleapis.com/v1beta1'
STATUS_PATH = 'status'
DEFAULT_TIMEOUT = '300'  # 5 minutes
DEFAULT_SUCCESS_NUMBER = 1
DEFAULT_FAILURE_NUMBER = 1


class PropertyError(Exception):
  """An exception raised when property values are invalid."""


def _ConfigName(context):
  """Return the short config name."""
  return '{}-config'.format(context.env['deployment'])


def _ConfigUrl(context):
  """Returns the full URL to the config, including hostname."""
  return '{endpoint}/projects/{project}/configs/{config}'.format(
      endpoint=RTC_ENDPOINT,
      project=context.env['project'],
      config=_ConfigName(context))


def _WaiterName(context):
  """Returns the short waiter name."""
  # This name is only used for the DM manifest entry. The actual waiter name
  # within RuntimeConfig is static, as it is scoped to the config resource.
  return '{}-software'.format(context.env['deployment'])


def _Timeout(context):
  """Returns the timeout property or a default value if unspecified."""
  timeout = context.properties.get('timeout', DEFAULT_TIMEOUT)
  try:
    return str(int(timeout))
  except ValueError:
    raise PropertyError('Invalid timeout value: {}'.format(timeout))


def _SuccessNumber(context):
  """Returns the successNumber property or a default value if unspecified."""
  number = context.properties.get('successNumber', DEFAULT_SUCCESS_NUMBER)
  try:
    number = int(number)
    if number < 1:
      raise PropertyError('successNumber value must be greater than 0.')
    return number
  except ValueError:
    raise PropertyError('Invalid successNumber value: {}'.format(number))


def _FailureNumber(context):
  """Returns the failureNumber property or a default value if unspecified."""
  number = context.properties.get('failureNumber', DEFAULT_FAILURE_NUMBER)
  try:
    number = int(number)
    if number < 1:
      raise PropertyError('failureNumber value must be greater than 0.')
    return number
  except ValueError:
    raise PropertyError('Invalid failureNumber value: {}'.format(number))


def _WaiterDependsOn(context):
  """Returns the waiterDependsOn property or an empty list if unspecified."""
  depends_on = context.properties.get('waiterDependsOn', [])
  if not isinstance(depends_on, list):
    raise PropertyError('waiterDependsOn must be a list: {}'.format(depends_on))

  for item in depends_on:
    if not isinstance(item, str):
      raise PropertyError(
          'waiterDependsOn must be a list of strings: {}'.format(depends_on))

  return depends_on


def _RuntimeConfig(context):
  """Constructs a RuntimeConfig resource."""

  deployment_name = context.env['deployment']
  return {
      'name': _ConfigName(context),
      'type': 'runtimeconfig.v1beta1.config',
      'properties': {
          'config': _ConfigName(context),
          'description': ('Holds software readiness status '
                          'for deployment {}').format(deployment_name),
      },
  }


def _Waiter(context):
  """Constructs a waiter resource."""

  waiter_timeout = _Timeout(context)
  return {
      'name': _WaiterName(context),
      'type': 'runtimeconfig.v1beta1.waiter',
      'metadata': {
          'dependsOn': _WaiterDependsOn(context),
      },
      'properties': {
          'parent': '$(ref.{}.name)'.format(_ConfigName(context)),
          'waiter': 'software',
          'timeout': '{}s'.format(waiter_timeout),
          'success': {
              'cardinality': {
                  'number': _SuccessNumber(context),
                  'path': '{}/success'.format(STATUS_PATH),
              },
          },
          'failure': {
              'cardinality': {
                  'number': _FailureNumber(context),
                  'path': '{}/failure'.format(STATUS_PATH),
              },
          },
      },
  }


def GenerateConfig(context):
  """Entry function to generate the DM config."""
  content = {
      'resources': [
          _RuntimeConfig(context),
          _Waiter(context),
      ],
      'outputs': [
          {
              'name': 'config-url',
              'value': _ConfigUrl(context)
          },
          {
              'name': 'variable-path',
              'value': STATUS_PATH
          },
      ]
  }
  return yaml.safe_dump(content)
