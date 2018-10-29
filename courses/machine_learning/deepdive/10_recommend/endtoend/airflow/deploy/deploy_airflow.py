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

"""
Script for deploying Apache Airflow on GKE.

  1) Provision and configure GCP resources
    a) Create a Cloud Storage bucket for DAGs, logs, etc.
    b) Create a GKE cluster
    c) Create a Cloud SQL DB for Airflow metadata
    d) Set the root password for the Cloud SQL DB
  2) Configure and launch Airflow components
    a) Push deployment-settings ConfigMap to GKE cluster
    b) Push Airflow configuration in ConfigMap to GKE cluster
    c) Create services for webserver, redis, and Cloud SQL proxy
    d) Create deployments for redis and Cloud SQL proxy
    e) Initialize DB and Web UI access password
    f) Create deployments for scheduler, workers, and webserver

Either set --output_settings or take note of the information in the
YAML dumped by this script, as it contains information needed to
identify resources to be cleaned up when it comes time to delete the
deployment.

Requirements to run:
  - gcloud & kubectl command-line tools
  - Python packages: oauth2client, retrying, yaml

Flags:
    --airflow_config: Path to config file for Airflow
    --settings: Path to YAML file containing deployment settings
    --output_settings: Path to which to save updated deployment
        settings. Note that these settings may include generated
        passwords. If not provided, prints to STDOUT.

Usage:
First make a copy of
//third_party/cloud/airflow/deploy/config/settings-template.yaml
(e.g., to ./config/settings.yaml), and make any desired modifications
(like setting the project name).
Then, run:
    python deploy_local.py --airflow_config config/airflow.cfg \
      --settings config/settings.yaml \
      --output_settings ./deployment-settings.yaml

Note that kubectl's current context will be changed to the newly-created
GKE instance.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import base64
import ConfigParser
import logging
import os
import random
import string
import subprocess
import sys
import tempfile
import traceback
import uuid

import gcp_util
import oauth2client.client
import retrying
import yaml


SERVICE_NAME = 'managed-airflow'

MAX_GCP_PROVISIONING_ATTEMTPS = 10

MAX_GKE_NAME_LENGTH = 40
MAX_GCS_BUCKET_LENGTH = 63
MAX_SQL_NAME_LENGTH = 80
MIN_LENGTH_LIMIT = min(MAX_GKE_NAME_LENGTH,
                       MAX_GCS_BUCKET_LENGTH,
                       MAX_SQL_NAME_LENGTH)

# Maximum interval between polling APIs
MAX_POLL_INTERVAL_SECS = 15

PASSWORD_CHARSET = string.ascii_letters + string.digits

logging.basicConfig(level=logging.INFO)


def _load_yaml(yaml_file):
    """Loads the contents of a YAML file into a Python object.

    Args:
        yaml_file: A string specifying the path to a YAML file.

    Returns:
        A Python dictionary representation of the loaded YAML file.
    """
    with open(yaml_file, 'r') as fd:
        try:
            return yaml.safe_load(fd)
        except yaml.YAMLError as e:
            logging.error('Error parsing YAML file : %s\n%s',
                          yaml_file, _format_traceback())
            raise e


def _generate_password(length=64):
    """Generates a random ASCII alphanumeric password.

    Args:
        length: an integer specifying the desired password length

    Returns:
        a password string
    """
    return ''.join(random.choice(PASSWORD_CHARSET) for _ in xrange(length))


def _format_traceback():
    _, _, tb = sys.exc_info()
    return ''.join(traceback.format_tb(tb))


@retrying.retry(wait_exponential_multiplier=1000,
                wait_exponential_max=MAX_POLL_INTERVAL_SECS * 1000,
                retry_on_result=(
                    lambda s: not s['status']['loadBalancer'].get('ingress')),
                retry_on_exception=lambda x: False)
def _get_loadbalancer_endpoint(service_name):
    """Poll a loadbalanced service for its endpoint.

    Args:
        service_name: a string specifying the name of the Kubernetes
            service whose loadbalancer endpoint to poll

    Returns:
        a dict representing the Kubernetes service, with an exposed
        endpoint
    """
    return yaml.safe_load(subprocess.check_output([
        'kubectl', 'get', 'svc', service_name, '-o', 'yaml']))


class LocalDeployment(object):
    """An instance of Airflow being deployed onto GCP."""

    def __init__(self, service_name, settings, airflow_config,
                 output_settings):
        """Initialize the deployment parameters.

        Args:
            service_name: a string to be used as a prefix for resources
                associated with this deployment. Keep it short, and for
                the least chance of failing name validation, stick to
                alphanumeric strings with dashes.
            settings: a dict containing desired settings for the
                deployment
            airflow_config: a string specifying the path to an Airflow
                config file to push to the instance
            output_settings: a string specifying a path to which to
                write updated deployment settings, or None if output to
                STDOUT is desired.
        """
        # string we can use to prefix instance names so that they are
        # associated with Airflow.
        self.service_name = service_name
        self.settings = settings  # dict representing the settings file.
        self.airflow_config = airflow_config  # string path to Airflow config
        self.output_settings = output_settings

        # string naming the GCP project
        self.project = settings['project']

        # string identifying GCP resources provisioned for this deployment
        self.id = None

        self._credentials = None

    def _make_settings_paths_absolute(self):
        """Converts paths in the deployment settings to aboslute paths.

        This is important because the contents of the deployment
        settings will be written out and referenced later. Converting
        any relative paths to absolute paths ensures that files
        referred to during deployment are the same as the ones referred
        to during teardown.
        """
        for kind in ('deployment', 'service', 'job'):
            self.settings['kubernetes'][kind] = dict(
                (k, os.path.abspath(v))
                for k, v
                in self.settings['kubernetes'][kind].iteritems())

    def _init_credentials(self):
        self._credentials = (
            oauth2client.client.GoogleCredentials.get_application_default())

    def deploy(self):
        """Deploys an instance of Airflow onto fresh GCP resources.

        Provisions and configures GCP resources and launches containers
        on GKE containing an Airflow deployment.

        If unexpected errors that we cannot recover from occur at any
        point, tears down all GCP resources to avoid resource leaks.

        Known issues:
          - Could get stuck in an infinite loop allocating GCP resources
            if provisioning fails for reasons beside name collision. See
            TODO in _provision_gcp().
          - Does not recover from any types of errors that occur while
            configuring Kubernetes to deploy Airflow. Kubernetes
            operations shouldn't really fail, so perhaps we should
            assume that failures are transient and just retry?
        """
        self._make_settings_paths_absolute()
        self._init_credentials()
        self._generate_passwords()

        self.id = self._provision_gcp()
        self.settings['id'] = self.id

        try:
            self._configure_kubectl()

            self._push_secrets()
            self._push_settings()
            self._push_airflow_config()

            self._create_services()
            self._deploy_redis()
            self._deploy_sql_proxy()
            self._initialize_deployment()
            self._deploy_scheduler()
            self._deploy_workers()
            self._deploy_webserver()
            self._get_webserver_endpoint()
        except Exception as e:
            # Unexpected exception during deployment of Airflow to the
            # cluster.  There's no good way to distinguish transient
            # failures from permanent ones in order to guide a retry
            # strategy, so teardown GCP resources then resume dying.
            logging.error('Error while deploying Airflow: %s\n%s',
                          e, _format_traceback())
            self._teardown_gcp(gcs_bucket=self.id, gke_cluster=self.id,
                               sql_instance=self.id)
            raise e

        self._output_settings()

    def _output_settings(self):
        """Dump deployment settings.

        The dumped settings can be used by callers to get the
        deployment ID an any passwords that may have been dynamically
        generated.
        """
        if self.output_settings:
            with open(self.output_settings, 'w') as fd:
                yaml.safe_dump(self.settings, stream=fd)
        else:
            yaml.safe_dump(self.settings, stream=sys.stdout)

    def _generate_id(self):
        """Generates an ID to be shared by all GCP resources.

        Each ID is formed from a common prefix, a delimiter, and a
        fixed-length suffix. In order to use the same ID for all
        associated GCP resources, we must comply with resource name
        length limits across all GCP products.
        Therefore, the length of the suffix is the longest possible
        length that complies with the shortest length limit.

        Returns:
          An identifier string that may or may not be available across
          all GCP resources that an Airflow instance will need to
          provision.
        """
        # Minus 1 for the hyphen delimiter.
        suffix_length = MIN_LENGTH_LIMIT - len(self.service_name) - 1
        return '%s-%s' % (self.service_name, uuid.uuid4().hex[:suffix_length])

    @retrying.retry(retry_on_result=lambda x: not x,
                    retry_on_exception=lambda x: False,
                    stop_max_attempt_number=MAX_GCP_PROVISIONING_ATTEMTPS)
    def _provision_gcp(self):
        """Provision GCP resources under a common ID string.

        Picks a common ID string and attempts to allocate a GCS bucket,
        spin up a GKE cluster, and create a Cloud SQL instance with
        that ID. If any provisioning step fails for any reason,
        GCP resources newly-provisioned by this invocation of this
        method are deleted.

        TODO(wwlian): This function makes no distinction between
        GCP provisioning failure due to name collision versus other
        reasons such as the project hitting quota.  Ideally, we'd
        retry indefinitely for name collision but only up to a certain
        number of times (possibly just once) for other types of
        failures. This will require some changes to the helpers in
        gcp_util to expose more information about provisioning failures.

        Returns:
            a non-empty common ID string under which GCP resources were
            successfully provisioned
        """
        candidate_id = self._generate_id()
        logging.info('Attempting GCP allocation with ID: %s', candidate_id)

        # Since GCS uses a global namespace, try it first so that
        # we catch collisions from outside this project before
        # allocating other resources.
        if not gcp_util.create_gcs_bucket(
                candidate_id, self.settings['gcs']['location'],
                self.project, self._credentials):
            return ''

        try:
            cluster_created = gcp_util.create_gke_cluster(
                candidate_id,
                self.project,
                self.settings['kubernetes']['zone'],
                self._credentials)
        except Exception as e:
            # An unexpected exception has occurred, so tear down
            # anything that might have been provisioned to prevent
            # resource leaks, then resume dying.
            logging.error('Error creating GKE cluster: %s\n%s',
                          e, _format_traceback())
            self._teardown_gcp(gcs_bucket=candidate_id,
                               gke_cluster=candidate_id)
            raise e

        if not cluster_created:
            self._teardown_gcp(gcs_bucket=candidate_id)
            return ''

        # Cloud SQL instance names cannot be recycled immediately,
        # so only try to provision the instance once the other
        # resources have been locked down.
        try:
            sql_created = (
                gcp_util.create_sql_instance(
                    candidate_id,
                    self.settings['cloud_sql']['region'],
                    self.settings['cloud_sql']['tier'],
                    self.project,
                    self._credentials)
                and gcp_util.set_sql_root_password(
                    self.settings['cloud_sql']['root_password'],
                    candidate_id,
                    self.project,
                    self._credentials))
        except Exception as e:
            # An unexpected exception has occurred, so tear down anything
            # that might # have been provisioned to prevent resource leaks,
            # then resume dying.
            logging.error('Error creating Cloud SQL instance: %s\n%s',
                          e, _format_traceback())
            self._teardown_gcp(gcs_bucket=candidate_id,
                               gke_cluster=candidate_id,
                               sql_instance=candidate_id)
            raise e

        if not sql_created:
            # Try to teardown the Cloud SQL instance in case it was created
            # but failed while trying to set the root password.
            self._teardown_gcp(gcs_bucket=candidate_id,
                               gke_cluster=candidate_id,
                               sql_instance=candidate_id)
            return ''

        logging.info('GCP resources successfully provisioned under ID: %s',
                     candidate_id)

        return candidate_id

    def _teardown_gcp(self, gcs_bucket=None, gke_cluster=None,
                      sql_instance=None):
        """Tears down GCP resources.

        If any arguments are None, no attempt will be made to tear down
        the corresponding resource type.

        Args:
            gcs_bucket: a string specifying the name of a GCS to delete
            gke_cluster: a string specifying the name of a GKE cluster
                to delete
            sql_instance: a string specifying the name of a Cloud SQL
                to delete
        """
        logging.info('Tearing down gcs_bucket=%s, gke_cluster=%s, '
                     'sql_instance=%s', gcs_bucket, gke_cluster, sql_instance)
        if gcs_bucket:
            gcp_util.delete_gcs_bucket(gcs_bucket, self._credentials,
                                       force=True)
        if gke_cluster:
            gcp_util.delete_gke_cluster(
                gke_cluster,
                self.project,
                self.settings['kubernetes']['zone'],
                self._credentials)
        if sql_instance:
            gcp_util.delete_sql_instance(sql_instance, self.project,
                                         self._credentials)

    def _generate_passwords(self):
        """Generates passwords for SQL and the web UI, if necessary.

        Tests whether passwords were provided in the settings file and
        generates any missing passwords.
        Any generated passwords are added into the self.settings object.

        In a production environment, we'll always want to
        dynamically-generate a unique password for each instance, but
        allowing passwords to appear in the settings file enables this
        script to be used against a partially-deployed managed Airflow
        instance (e.g., by commenting out or otherwise disabling
        _provision_gcp()).
        """
        self.settings['cloud_sql'].setdefault('root_password',
                                              _generate_password())
        self.settings['cloud_sql'].setdefault('password', _generate_password())
        self.settings.setdefault('web_ui_password', _generate_password())

    def _configure_kubectl(self):
        """Configures kubectl to access the recently-provisioned GKE cluster.
        """
        subprocess.check_call([
            'gcloud', 'container', 'clusters', 'get-credentials', self.id,
            '--zone', self.settings['kubernetes']['zone'],
            '--project', self.project])

    def _push_secrets(self):
        """Pushes passwords to the GKE cluster.

        Kubernetes requires secrets created from a config file to be
        base64-encoded. They are automatically decoded when accessed
        on the cluster.
        """
        b64e = base64.b64encode
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': 'deployment-secrets'
            },
            'type': 'Opaque',
            'data': {
                'sql_root_password':
                    b64e(self.settings['cloud_sql']['root_password']),
                'sql_password':
                    b64e(self.settings['cloud_sql']['password']),
                'web_ui_password':
                    b64e(self.settings['web_ui_password'])
            }
        }

        p = subprocess.Popen(['kubectl', 'create', '-f', '-'],
                             stdin=subprocess.PIPE)
        try:
            p.communicate(input=yaml.dump(secret))
        except yaml.YAMLError as e:
            logging.error(
                'Error creating Secret deployment-secrets: %s\n%s',
                e, _format_traceback())
            raise e

    def _push_settings(self):
        """Pushes deployment settings to the GKE cluster.

        Deployment settings includes information needed to connect to
        the Cloud SQL database as well as the name of the GCS bucket.
        """
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'data': {},
            'metadata': {
                'name': 'deployment-settings',
            }
        }

        configmap['data']['sql_project'] = self.project
        configmap['data']['sql_region'] = self.settings['cloud_sql']['region']
        configmap['data']['sql_instance'] = self.id
        configmap['data']['sql_database'] = (
                self.settings['cloud_sql']['database'])
        configmap['data']['sql_root_user'] = (
                self.settings['cloud_sql']['root_user'])
        configmap['data']['sql_user'] = self.settings['cloud_sql']['user']

        configmap['data']['gcs_bucket'] = self.id

        configmap['data']['web_ui_username'] = self.settings['web_ui_username']

        configmap['data']['gcp_project'] = self.project

        config = ConfigParser.ConfigParser()
        with open(self.airflow_config) as fd:
            config.readfp(fd)
        configmap['data']['airflow_home'] = config.get('core', 'airflow_home')
        configmap['data']['dags_folder'] = config.get('core', 'dags_folder')

        p = subprocess.Popen(['kubectl', 'create', '-f', '-'],
                             stdin=subprocess.PIPE)
        try:
            p.communicate(input=yaml.dump(configmap))
        except yaml.YAMLError as e:
            logging.error(
                'Error creating ConfigMap deployment-settings: %s\n%s',
                e, _format_traceback())
            raise e

    def _push_airflow_config(self):
        """Pushes the config file for Airflow to the GKE cluster."""
        config = ConfigParser.ConfigParser()
        with open(self.airflow_config) as fd:
            config.readfp(fd)
        config.set('core', 'remote_base_log_folder', 'gs://%s/logs' % self.id)

        tmp = tempfile.NamedTemporaryFile()
        config.write(tmp)
        tmp.flush()
        subprocess.call([
            'kubectl', 'create', 'configmap', 'airflow-config', '--from-file',
            'airflow.cfg=' + tmp.name])

    def _create_services(self):
        """Creates services in the GKE cluster."""
        subprocess.call(['kubectl', 'create', '-f',
                         self.settings['kubernetes']['service']['sql_proxy']])
        subprocess.call(['kubectl', 'create', '-f',
                         self.settings['kubernetes']['service']['redis']])
        subprocess.call(['kubectl', 'create', '-f',
                         self.settings['kubernetes']['service']['webserver']])

    def _get_webserver_endpoint(self):
        """Retrieves the URL at which the Airflow web UI can be accessed."""
        with open(self.settings['kubernetes']['service']['webserver'],
                  'r') as fd:
            try:
                service_spec = yaml.safe_load(fd.read())
            except yaml.YAMLError as e:
                logging.error(
                    'Invalid webserver spec: %s\n%s',
                    self.settings['kubernetes']['service']['webserver'],
                    _format_traceback())
                raise e

        service = _get_loadbalancer_endpoint(service_spec['metadata']['name'])
        self.settings['web_ui_url'] = 'http://%s:%s' % (
            service['status']['loadBalancer']['ingress'][0]['ip'],
            service['spec']['ports'][0]['port'])

    def _deploy_redis(self):
        """Creates a redis deployment in the GKE cluster."""
        subprocess.call(['kubectl', 'create', '-f',
                         self.settings['kubernetes']['deployment']['redis']])

    def _deploy_sql_proxy(self):
        """Creates a SQL proxy deployment in the GKE cluster.
        """
        subprocess.call([
            'kubectl', 'create', '-f',
            self.settings['kubernetes']['deployment']['sql_proxy']])

    def _deploy_scheduler(self):
        """Creates an Airflow scheduler deployment in the GKE cluster."""
        subprocess.call([
            'kubectl', 'create', '-f',
            self.settings['kubernetes']['deployment']['scheduler']])

    def _deploy_workers(self):
        """Creates an Airflow worker deployment in the GKE cluster."""
        subprocess.call(['kubectl', 'create', '-f',
                         self.settings['kubernetes']['deployment']['workers']])

    def _deploy_webserver(self):
        """Creates an Airflow web UI webserver in the GKE cluster."""
        subprocess.call([
            'kubectl', 'create', '-f',
            self.settings['kubernetes']['deployment']['webserver']])

    def _initialize_deployment(self):
        """Kicks off a job to initialize the Airflow deployment.

        The initialization job does 3 things:
        * Initializes the database with a user and tables for Airflow.
        * Sets up password authentication for the web UI.
        * Sets the project field in the default Airflow Connections
            related to GCP.

        .. note::
        Password authentication is a stopgap measure to protect the
        WebUI, which will be exposed to the public internet via the
        webserver service.  In production, the service probably won't be
        exposed to the public web, and authentication will make use of
        IAM roles in the project.
        """
        subprocess.call(['kubectl', 'create', '-f',
                         self.settings['kubernetes']['job']['init']])


def main():
    args = _parse_args()
    logging.basicConfig(level=getattr(logging, args.log))

    settings = _load_yaml(args.settings)
    deployment = LocalDeployment(SERVICE_NAME, settings, args.airflow_config,
                                 args.output_settings)
    deployment.deploy()


def _existing_filepath(val):
    if os.path.isfile(val):
        return val
    raise argparse.ArgumentError('Path is not an existing file: %s' % val)


def _log_level_str(level):
    level_num = getattr(logging, level.upper(), None)
    if not isinstance(level_num, int):
        raise argparse.ArgumentError('Invalid log level: %s' % level)
    return level.upper()


def _parse_args():
    parser = argparse.ArgumentParser(description='Deploy Airflow on GCP')
    parser.add_argument(
        '--airflow_config', help='Path to config file for Airflow',
        type=_existing_filepath, required=True)
    parser.add_argument(
        '--settings', help='Path to YAML file containing deployment settings',
        type=_existing_filepath, required=True)
    parser.add_argument(
        '--output_settings', help='Path to which to save updated deployment '
        'settings. Note that these settings may include generated passwords. '
        'If not provided, prints to STDOUT.')

    # Because argparse renders the helpstring (which we want to
    # contain the string-versions of levels) from the
    # choices set and runs the type function prior to checking for membership
    # in the choices set, the type function must return the same type as
    # members of the choices set. Therefore, the type is string rather than
    # enum (int).
    parser.add_argument('--log',
                        help='The logging level to use. (default: INFO)',
                        choices=set(['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                     'CRITICAL']),
                        type=_log_level_str, default='INFO')
    return parser.parse_args()


if __name__ == '__main__':
    main()
