# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Airflow plugin for Google App Engine Admin functions."""

from airflow.contrib.hooks.gcp_api_base_hook import GoogleCloudBaseHook
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from apiclient.discovery import build
from datetime import datetime
from googleapiclient import errors

import logging
from oauth2client.client import GoogleCredentials
import time


class AppEngineAdminHook(GoogleCloudBaseHook):
  """Hook for App Engine Flex Admin."""

  def __init__(self, gcp_conn_id='google_cloud_default', delegate_to=None):
    super(AppEngineAdminHook, self).__init__(gcp_conn_id, delegate_to)
    self._gaeadmin = self.get_ae_conn()
    self._svcadmin = self.get_svc_conn()

  def get_ae_conn(self):
    """Returns: a App Engine service object."""
    credentials = GoogleCredentials.get_application_default()
    return build('appengine', 'v1', credentials=credentials)

  def get_svc_conn(self):
    """Returns: a Services Management service object."""
    credentials = GoogleCredentials.get_application_default()
    return build('servicemanagement', 'v1', credentials=credentials)

  def create_version(self, project_id, service_id, version_spec):
    """Creates new service version on App Engine Engine.

    Args:
      project_id: project id
      service_id: service id
      version_spec: app version spec

    Returns:
      The operation if the version was created successfully and
      raises an error otherwise.
    """
    create_request = self._gaeadmin.apps().services().versions().create(
        appsId=project_id, servicesId=service_id, body=version_spec)
    response = create_request.execute()
    op_name = response['name'].split('/')[-1]
    return self._wait_for_operation_done(project_id, op_name)

  def migrate_traffic(self, project_id, service_id, new_version):
    """Migrate AE traffic from current version to new version.

    Args:
      project_id: project id
      service_id: service id
      new_version: new version id

    Returns:
      the operation if the migration was successful and
      raises an error otherwise.
    """
    split_config = {'split': {'allocations': {new_version: '1'}}}
    migrate_request = self._gaeadmin.apps().services().patch(
        appsId=project_id, servicesId=service_id, updateMask='split',
        body=split_config)
    response = migrate_request.execute()
    op_name = response['name'].split('/')[-1]
    return self._wait_for_operation_done(project_id, op_name)

  def get_endpoint_config(self, service_id):
    """Get latest endpoint config for an endpoint service.

    Args:
      service_id: service id

    Returns:
      the config version if successful and raises an error otherwise.
    """
    resource = self._svcadmin.services().rollouts()
    list_request = resource.list(serviceName=service_id)
    response = list_request.execute()
    config_id = response['rollouts'][0]['rolloutId']

    return config_id

  def get_version(self, project_id, service_id, version):
    """Get spec for a version of a service on App Engine Engine.

    Args:
      project_id: project id
      service_id: service id
      version: version id

    Returns:
      the version spec if successful and raises an error otherwise.
    """
    resource = self._gaeadmin.apps().services().versions()
    get_request = resource.get(appsId=project_id, servicesId=service_id,
                               versionsId=version, view='FULL')
    response = get_request.execute()

    return response

  def get_version_identifiers(self, project_id, service_id):
    """Get list of versions of a service on App Engine Engine.

    Args:
      project_id: project id
      service_id: service id

    Returns:
      the list of version identifiers if successful and raises an error otherwise.
    """
    request = self._gaeadmin.apps().services().versions().list(appsId=project_id,
                                                               servicesId=service_id)
    versions = []
    while request is not None:
      versions_doc = request.execute()
      versions.extend([v['id'] for v in versions_doc['versions']])
      request = self._gaeadmin.apps().services().versions().list_next(request,
                                                                      versions_doc)

    return versions

  def _get_operation(self, project_id, op_name):
    """Gets an AppEngine operation based on the operation name.

    Args:
      project_id: project id
      op_name: operation name

    Returns:
      AppEngine operation object if succeed.

    Raises:
      apiclient.errors.HttpError: if HTTP error is returned from server
    """
    resource = self._gaeadmin.apps().operations()
    request = resource.get(appsId=project_id, operationsId=op_name)
    return request.execute()

  def _wait_for_operation_done(self, project_id, op_name, interval=30):
    """Waits for the Operation to reach a terminal state.

    This method will periodically check the job state until the operation reaches
    a terminal state.

    Args:
      project_id: project id
      op_name: operation name
      interval: check interval in seconds

    Returns:
      AppEngine operation object if succeed.

    Raises:
      apiclient.errors.HttpError: if HTTP error is returned when getting
      the operation
    """
    assert interval > 0
    while True:
      operation = self._get_operation(project_id, op_name)
      if 'done' in operation and operation['done']:
        return operation
      time.sleep(interval)


class AppEngineVersionOperator(BaseOperator):
  """Operator for creating a new AppEngine flex service version."""

  @apply_defaults
  def __init__(self,
               project_id,
               service_id,
               region,
               service_spec=None,
               gcp_conn_id='google_cloud_default',
               delegate_to=None,
               *args,
               **kwargs):
    super(AppEngineVersionOperator, self).__init__(*args, **kwargs)
    self._project_id = project_id
    self._service_id = service_id
    self._region = region

    self._service_spec = service_spec
    self._gcp_conn_id = gcp_conn_id
    self._delegate_to = delegate_to

    if not self._project_id:
      raise AirflowException('Cloud project id is required.')
    if not self._service_id:
      raise AirflowException('App Engine service name is required.')
    if not self._region:
      raise AirflowException('Compute Engine region is required.')

  def execute(self, context):
    hook = AppEngineAdminHook(
        gcp_conn_id=self._gcp_conn_id, delegate_to=self._delegate_to)

    # if version spec is not provided, use spec for latest version
    if self._service_spec is None:
      # get version spec for latest version, assuming version ids are sortable
      version_list = hook.get_version_identifiers(self._project_id,
                                                  self._service_id)
      latest_version = max(version_list)
      version_spec = hook.get_version(self._project_id, self._service_id,
                                      latest_version)

      # get endpoints config id
      endpoint_service = '{0}.appspot.com'.format(self._project_id)
      config_id = hook.get_endpoint_config(endpoint_service)

      # clean irrelevant params
      version_spec.pop('name', None)
      version_spec.pop('threadsafe', None)
      version_spec.pop('servingStatus', None)
      version_spec.pop('createTime', None)
      version_spec.pop('createdBy', None)
      version_spec.pop('runtimeApiVersion', None)
      version_spec.pop('versionUrl', None)
      version_spec.pop('betaSettings', None)

      # fix docker container ref
      container_ref = version_spec['deployment']['container']['image']
      container_ref = container_ref.split('@sha')[0]
      version_spec['deployment']['container']['image'] = container_ref

      # add endpoint service params
      version_spec.update({'endpointsApiService': {
          'name': '{0}.appspot.com'.format(self._project_id),
          'configId': config_id
      }})
    else:
      version_spec = self._version_spec

    if 'id' not in version_spec:
      # generate version id and add to params
      now = datetime.now()
      version_spec['id'] = '{0}t{1}'.format(now.strftime('%Y%m%d'),
                                            now.strftime('%H%M%S'))

    # deploy new version
    try:
      finished_version_op = hook.create_version(self._project_id,
                                                self._service_id, version_spec)
    except errors.HttpError:
      raise

    if 'error' in finished_version_op:
      logging.error('AppEngine version deploy failed: %s',
                    str(finished_version_op))
      raise RuntimeError(finished_version_op['error']['message'])

    # migrate traffic to new version
    new_version = version_spec['id']
    try:
      finished_migrate_op = hook.migrate_traffic(self._project_id,
                                                 self._service_id, new_version)
    except errors.HttpError:
      raise

    if 'error' in finished_migrate_op:
      logging.error('AppEngine version migrate failed: %s',
                    str(finished_version_op))
      raise RuntimeError(finished_migrate_op['error']['message'])


# Plugin class for GAEAdmin
class AppEngineAdminPlugin(AirflowPlugin):
  name = 'app_engine_admin_plugin'
  operators = [AppEngineVersionOperator]
  hooks = [AppEngineAdminHook]
  executors = []
  macros = []
  admin_views = []
  flask_blueprints = []
  menu_links = []

