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

"""Airflow plugin for ML Engine, backported from v1.9."""

from airflow.contrib.hooks.gcp_api_base_hook import GoogleCloudBaseHook
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

from apiclient.discovery import build
from googleapiclient import errors

import logging
from oauth2client.client import GoogleCredentials
import re
import time


class MLEngineHook(GoogleCloudBaseHook):
  """Hook for ML Engine."""

  def __init__(self, gcp_conn_id='google_cloud_default', delegate_to=None):
    super(MLEngineHook, self).__init__(gcp_conn_id, delegate_to)
    self._mlengine = self.get_conn()

  def normalize_mlengine_job_id(self, job_id):
    """Replaces invalid MLEngine job_id characters with '_'.

    This also adds a leading 'z' in case job_id starts with an invalid
    character.

    Args:
        job_id: A job_id str that may have invalid characters.

    Returns:
        A valid job_id representation.
    """
    match = re.search(r'\d', job_id)
    if match and match.start() is 0:
      job_id = 'z_{}'.format(job_id)
    return re.sub('[^0-9a-zA-Z]+', '_', job_id)

  def get_conn(self):
    """Returns a Google MLEngine service object."""
    credentials = GoogleCredentials.get_application_default()
    return build('ml', 'v1', credentials=credentials)

  def create_job(self, project_id, job, use_existing_job_fn=None):
    """Launches a MLEngine job and wait for it to reach a terminal state.

    Args:
      project_id: project id
      job: job name
      use_existing_job_fn: existing job to use

    Returns:
        The MLEngine job object if the job successfully reach a
        terminal state (which might be FAILED or CANCELLED state).
    """
    request = self._mlengine.projects().jobs().create(
        parent='projects/{}'.format(project_id),
        body=job)
    job_id = job['jobId']

    try:
      request.execute()
    except errors.HttpError as e:
      # 409 means there is an existing job with the same job ID.
      if e.resp.status == 409:
        if use_existing_job_fn is not None:
          existing_job = self._get_job(project_id, job_id)
          if not use_existing_job_fn(existing_job):
            logging.error(
                'Job with job_id %s already exist, but it does '
                'not match our expectation: %s',
                job_id, existing_job
            )
            raise
        logging.info(
            'Job with job_id %s already exist. Will waiting for it to finish',
            job_id
        )
      else:
        logging.error('Failed to create MLEngine job: %s', e)
        raise

    return self._wait_for_job_done(project_id, job_id)

  def _get_job(self, project_id, job_id):
    """Gets a MLEngine job based on the job name.

    Args:
      project_id: project id
      job_id: job id

    Returns:
      MLEngine job object if succeed.

    Raises:
        apiclient.errors.HttpError: if HTTP error is returned from server
    """
    job_name = 'projects/{}/jobs/{}'.format(project_id, job_id)
    request = self._mlengine.projects().jobs().get(name=job_name)
    while True:
      try:
        return request.execute()
      except errors.HttpError as e:
        if e.resp.status == 429:
          # polling after 30 seconds when quota failure occurs
          time.sleep(30)
        else:
          logging.error('Failed to get MLEngine job: %s', e)
          raise

  def _wait_for_job_done(self, project_id, job_id, interval=30):
    """Waits for the Job to reach a terminal state.

    This method will periodically check the job state until the job reach
    a terminal state.

    Args:
      project_id: project id
      job_id: job id
      interval: check interval in seconds

    Returns:
      MLEngine job object if succeed.

    Raises:
        apiclient.errors.HttpError: if HTTP error is returned when getting
        the job
    """
    assert interval > 0
    while True:
      job = self._get_job(project_id, job_id)
      if job['state'] in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
        return job
      time.sleep(interval)


class MLEngineTrainingOperator(BaseOperator):
  """Operator for launching a MLEngine training job.
  """

  @apply_defaults
  def __init__(self,
               project_id,
               job_id,
               package_uris,
               training_python_module,
               training_args,
               region,
               scale_tier=None,
               master_type=None,
               gcp_conn_id='google_cloud_default',
               delegate_to=None,
               mode='PRODUCTION',
               *args,
               **kwargs):
    super(MLEngineTrainingOperator, self).__init__(*args, **kwargs)
    self._project_id = project_id
    self._job_id = job_id
    self._package_uris = package_uris
    self._training_python_module = training_python_module
    self._training_args = training_args
    self._region = region
    self._scale_tier = scale_tier
    self._master_type = master_type
    self._gcp_conn_id = gcp_conn_id
    self._delegate_to = delegate_to
    self._mode = mode

    if not self._project_id:
      raise AirflowException('Google Cloud project id is required.')
    if not self._job_id:
      raise AirflowException(
          'An unique job id is required for Google MLEngine training '
          'job.')
    if not package_uris:
      raise AirflowException(
          'At least one python package is required for MLEngine '
          'Training job.')
    if not training_python_module:
      raise AirflowException(
          'Python module name to run after installing required '
          'packages is required.')
    if not self._region:
      raise AirflowException('Google Compute Engine region is required.')

  def execute(self, context):
    hook = MLEngineHook(
        gcp_conn_id=self._gcp_conn_id, delegate_to=self._delegate_to)

    job_id = hook.normalize_mlengine_job_id(self._job_id)
    training_request = {
        'jobId': job_id,
        'trainingInput': {
            'scaleTier': self._scale_tier,
            'packageUris': self._package_uris,
            'pythonModule': self._training_python_module,
            'region': self._region,
            'args': self._training_args,
            'masterType': self._master_type
        }
    }

    if self._mode == 'DRY_RUN':
      logging.info('In dry_run mode.')
      logging.info('MLEngine Training job request is: %s', training_request)
      return

    # Helper method to check if the existing job's training input is the
    # same as the request we get here.
    def check_existing_job(existing_job):
      return (existing_job.get('trainingInput', None)
              == training_request['trainingInput'])

    try:
      finished_training_job = hook.create_job(
          self._project_id, training_request, check_existing_job)
    except errors.HttpError:
      raise

    if finished_training_job['state'] != 'SUCCEEDED':
      logging.error('MLEngine training job failed: %s',
                    str(finished_training_job))
      raise RuntimeError(finished_training_job['errorMessage'])


# Plugin class for GoogleMLEngine
class GoogleMLEnginePlugin(AirflowPlugin):
  name = 'ml_engine_plugin'
  operators = [MLEngineTrainingOperator]
  hooks = [MLEngineHook]
  executors = []
  macros = []
  admin_views = []
  flask_blueprints = []
  menu_links = []
