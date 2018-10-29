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

"""Script for tearing down an Airflow deployment on GCP.

This script essentially just tears down the GCP resources.
It does not interact with Kubernetes or Airflow.

The cluster to tear down is specified via the deployment settings

Flags:
    --settings: Path to YAML file containing deployment settings.
        file emitted by the deployment script.
"""

import argparse
import logging
import os
import subprocess
import time

import gcp_util
import oauth2client.client
import yaml


def _delete_service(service_file):
    """Deletes a Kubernetes service.

    Args:
        service_file: a string specifying the path to the file used to
            create the service to be deleted
    """
    subprocess.call(['kubectl', 'delete', '-f', service_file])


def main():
    args = _parse_args()
    logging.basicConfig(level=args.log)

    credentials = (
            oauth2client.client.GoogleCredentials.get_application_default())

    with open(args.settings, 'r') as fd:
        settings = yaml.safe_load(fd)

    # Explicitly deleting the service causes Kubernetes to delete the
    # forwarding rule and target pool created for it, which would
    # otherwise stick around if we deleted the GKE cluster straightaway.
    # The need to do this is a consequence of a known GKE bug.
    logging.info('Halting webserver service')
    _delete_service(settings['kubernetes']['service']['webserver'])
    # Sleep so that the service can clean up networking resources
    # before the cluster gets torn down.
    # TODO(wwlian): Do something more elegant like polling the GCE API
    # for when the target pool and forwarding rule have successfully
    # been taken down.
    time.sleep(10)

    logging.info('Deleting GKE cluster: %s', settings['id'])
    outcome = gcp_util.delete_gke_cluster(
        settings['id'],
        settings['project'],
        settings['kubernetes']['zone'],
        credentials)
    logging.info('Success' if outcome else 'Failed')

    logging.info('Deleting GCS bucket: %s', settings['id'])
    outcome = gcp_util.delete_gcs_bucket(settings['id'], credentials,
                                         force=True)
    logging.info('Success' if outcome else 'Failed')

    logging.info('Deleting Cloud SQL instance: %s', settings['id'])
    outcome = gcp_util.delete_sql_instance(settings['id'],
                                           settings['project'],
                                           credentials)
    logging.info('Success' if outcome else 'Failed')


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
    parser = argparse.ArgumentParser(description='Tear down Airflow on GCP')
    parser.add_argument(
        '--settings', help='Path to YAML file containing deployment settings',
        type=_existing_filepath, required=True)

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
