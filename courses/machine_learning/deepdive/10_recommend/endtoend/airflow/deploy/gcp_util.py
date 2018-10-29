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

"""Helper functions for interacting with Google Cloud Platform APIs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import time

from apiclient import discovery
import apiclient.errors


# Cap exponential backoff for polling APIs
MAX_POLL_INTERVAL_SECS = 15


def empty_gcs_bucket(bucket_name, credentials):
    """Attempts to delete all objects in a bucket.

    If concurrent object creations occur while the bucket is being
    emptied, those objects may not be deleted and may cause bucket
    deletion to fail.

    Args:
        bucket_name: a string specifying the bucket to empty
        credentials: oauth2client.Credentials to be used for
            authentication
    """
    logging.info("Emptying GCS bucket: %s", bucket_name)
    service = discovery.build('storage', 'v1', credentials=credentials)
    response = service.objects().list(bucket=bucket_name).execute()
    _delete_resources(bucket_name, response.get('items', []), credentials)
    while 'nextPageToken' in response:
        response = service.objects().list(
            bucket=bucket_name, pageToken=response['nextPageToken']).execute()
        _delete_resources(bucket_name, response.get('items', []), credentials)


def _delete_resources(bucket_name, resources, credentials):
    """Deletes the specified resources from the given bucket.

    Resources are represented as described in
    https://cloud.google.com/storage/docs/json_api/v1/objects#resource

    Args:
        bucket_name: a string specifying the bucket from which to
            delete
        resources: a list of resources
        credentials: oauth2client.Credentials to be used for
            authentication
    """
    logging.info("Deleting %s resources.", len(resources))
    service = discovery.build('storage', 'v1', credentials=credentials)
    for r in resources:
        try:
            service.objects().delete(
                bucket=bucket_name,
                object=r['name']).execute()
        except apiclient.errors.HttpError as e:
            logging.warning('Error deleting %s: %s', r, e)


def create_gcs_bucket(bucket_name, location, project, credentials):
    """Attempts to create a Google Cloud Storage bucket.

    Args:
        bucket_name: a string specifying the name of the bucket to
            create
        location: a string specifying the location where the bucket
            should be allocated. See
            https://cloud.google.com/storage/docs/bucket-locations
            for an authoritative list of values.
        project: a string specifying the GCP project in which to create
            the bucket
        credentials: oauth2client.Credentials to be used for
            authentication

    Returns:
        True if a bucket named bucket_name was successfully created, False
        otherwise. Note that False will be returned if there was already a
        bucket with the provided bucket_name.
    """
    service = discovery.build('storage', 'v1', credentials=credentials)
    body = {'name': bucket_name, 'location': location}
    try:
        service.buckets().insert(project=project, body=body).execute()
        logging.info('Created GCS bucket gs://%s', bucket_name)
        return True
    except apiclient.errors.HttpError as e:
        logging.warn('Failed to create GCS bucket gs://%s. %s', bucket_name, e)
        return False


def delete_gcs_bucket(bucket_name, credentials, force=False):
    """Attempts to delete a Google Cloud Storage bucket.

    The REST API doesn't allow for deletion of non-empty buckets;
    use force=True to attempt to empty the bucket prior to deletion.
    If concurrent object creations occur while the bucket is being
    emptied, those objects may not be deleted and may cause bucket
    deletion to fail.

    Args:
        bucket_name: a string specifying the name of the bucket to
            delete
        credentials: oauth2client.Credentials to be used for
            authentication
        force: a boolean specifying whether or not to attempt to empty
            the bucket prior to deletion.

    Returns:
        True if a bucket named bucket_name was successfully deleted, False
        otherwise.
    """
    if force:
        empty_gcs_bucket(bucket_name, credentials)

    service = discovery.build('storage', 'v1', credentials=credentials)
    try:
        resp = service.buckets().delete(bucket=bucket_name).execute()
        # An empty response indicates a successful deletion.
        # https://cloud.google.com/storage/docs/json_api/v1/buckets/delete
        return not bool(resp)
    except apiclient.errors.HttpError as e:
        logging.warn('Error deleting GCS bucket %s: %s', bucket_name, e)
        return False


def create_gke_cluster(cluster_name, project, zone, credentials):
    """Tries to create a GKE cluster.

    TODO(wwlian): Expose more of the node pool's configuration as
                  needed.

    Args:
        cluster_name: string specifying the desired cluster name
        project: a string specifying the GCP project in which to create
            the cluster
        zone: string specifying the GCE zone in which to create the
            cluster
        credentials: oauth2client.Credentials to be used for
            authentication

    Returns:
        True if a new cluster with the provided name has been created,
        False otherwise. Note that False will be returned if a cluster
        with the provided cluster_name already existed.
    """
    service = discovery.build('container', 'v1', credentials=credentials)
    cluster_body = {
        'name': cluster_name,
        'zone': zone,
        'network': 'default',
        'loggingService': 'logging.googleapis.com',
        'monitoringService': 'none',
        'subnetwork': 'default',
        'nodePools': [{
            'initialNodeCount': 3,
            'config': {
                'machineType': 'n1-standard-1',
                'imageType': 'GCI',
                'diskSizeGb': 100,
                'oauthScopes': [
                    'https://www.googleapis.com/auth/compute',
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    'https://www.googleapis.com/auth/sqlservice.admin',
                    'https://www.googleapis.com/auth/logging.write',
                    'https://www.googleapis.com/auth/servicecontrol',
                    'https://www.googleapis.com/auth/service.management.'
                    'readonly',
                    'https://www.googleapis.com/auth/trace.append',
                    'https://www.googleapis.com/auth/source.read_only',
                    'https://www.googleapis.com/auth/cloud-platform'
                ]
            },
            'autoscaling': {
                'enabled': False
            },
            'management': {
                'autoUpgrade': False,
                'autoRepair': False,
                'upgradeOptions': {}
            },
            'name': 'default-pool'
        }],
        'masterAuth': {
            'username': 'admin'
        }
    }

    request = service.projects().zones().clusters().create(
        projectId=project, zone=zone, body={'cluster': cluster_body})

    logging.info('Waiting for GKE cluster creation: %s', cluster_name)
    if not _wait_for_operation(request,
                               _gke_op_poller_factory(service, project, zone)):
        logging.warn('GKE cluster creation failed: %s', cluster_name)
        return False

    # Verify creation by tring to retrieve cluster info.
    request = service.projects().zones().clusters().get(
        projectId=project, zone=zone, clusterId=cluster_name)
    try:
        request.execute()
        logging.info('Created GKE cluster: %s', cluster_name)
        return True
    except apiclient.errors.HttpError as e:
        logging.warn(str(e))
        return False


def delete_gke_cluster(cluster_name, project, zone, credentials):
    """Attempts to delete a GKE cluster.

    Args:
        cluster_name: A string specifying the cluster to delete
        project: a string specifying the GCP project in which the
            cluster resides
        zone: The zone from which to delete the cluster
        credentials: oauth2client.Credentials to be used for
            authentication

    Returns:
        True if the specified cluster was successfully deleted from the
        specified zone; False otherwise.
    """
    service = discovery.build('container', 'v1', credentials=credentials)

    # If the cluster is in the process of being provisioned, we have to wait
    # until it is up and running before we can initiate deletion.
    request = service.projects().zones().clusters().get(
        projectId=project, zone=zone, clusterId=cluster_name)
    while True:
        try:
            cluster = request.execute()
        except apiclient.errors.HttpError:
            # No such cluster; this will get caught when we try to delete
            # it.
            break
        if cluster['status'] == 'RUNNING':
            break

    request = service.projects().zones().clusters().delete(
        projectId=project, zone=zone, clusterId=cluster_name)

    if not _wait_for_operation(
            request, _gke_op_poller_factory(service, project, zone)):
        return False

    # Verify deletion by tring to retrieve cluster info.
    request = service.projects().zones().clusters().get(
        projectId=project, zone=zone, clusterId=cluster_name)
    try:
        request.execute()
        return False
    except apiclient.errors.HttpError as e:
        return e.resp['status'] == '404'


def create_sql_instance(instance_name, db_region, db_tier, project,
                        credentials):
    """Creates a Cloud SQL instance and sets its root password.

    If the instance already exists, the creation step is skipped, but
    the root password will still be reset.

    Args:
        instance_name: A string specifying the name for the new instance
        db_region: A string specifying the region in which the instance
            should be created
        db_tier: A string specifying the database tier to create. For a
            list of valid tiers and the regions in which they are
            available, use 'gcloud sql tiers list'.
        project: a string specifying the GCP project in which to create
            the instance credentials: oauth2client.Credentials to be
            used for authentication

    Returns:
        True if the Cloud SQL instance was successfully created, and its
        root password was successfully set; False otherwise.
    """
    service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)
    request = service.instances().insert(
        project=project,
        body={
            'name': instance_name,
            'region': db_region,
            'settings': {
                'tier': db_tier,
                'activationPolicy': 'ALWAYS'
            }
        }
    )

    logging.info('Waiting for Cloud SQL instance creation: %s', instance_name)
    if not _wait_for_operation(request,
                               _cloud_sql_op_poller_factory(service, project)):
        return False

    # Verify creation by tring to retrieve instance info.
    request = service.instances().get(project=project,
                                      instance=instance_name)
    try:
        request.execute()
        return True
    except apiclient.errors.HttpError:
        return False


def set_sql_root_password(root_pw, instance_name, project, credentials):
    """Attempts to set the root SQL password in a Cloud SQL instance.

    Args:
        root_pw: A string specifying the root password to set in the
            Cloud SQL instance.
        instance_name: A string specifying the name of the Cloud SQL
            instance
        project: a string specifying the GCP project in which to create
            the instance
        credentials: oauth2client.Credentials to be used for
            authentication

    Returns:
        True if the instance's root password was successfully set; False
        otherwise.
    """
    service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)
    request = service.users().update(
        project=project, instance=instance_name, host='%', name='root',
        body={'password': root_pw})

    logging.info('Waiting for Cloud SQL root password set: %s', instance_name)
    return _wait_for_operation(request,
                               _cloud_sql_op_poller_factory(service, project))


def delete_sql_instance(instance_name, project, credentials):
    """Attempts to delete a Google Cloud SQL instance.

    Args:
        instance_name: A string specifying the name for the new instance
        project: a string specifying the GCP project in which the
            instance resides
        credentials: oauth2client.Credentials to be used for
            authentication

    Returns:
        True if this attempt to delete the instance succeeded, False
        otherwise.  Note that this means that this function may return
        False if the instance did not exist in the first place or was
        deleted concurrently
    """
    service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)

    # If the instance is in the process of being provisioned, we have to
    # wait until it is up and running before we can initiate deletion.
    request = service.instances().get(project=project, instance=instance_name)
    while True:
        try:
            instance = request.execute()
        except apiclient.errors.HttpError:
            # No such instance; this will get caught when we try to delete
            # it.
            break
        if instance['state'] == 'RUNNABLE':
            break

    request = service.instances().delete(project=project,
                                         instance=instance_name)

    if not _wait_for_operation(
            request, _cloud_sql_op_poller_factory(service, project)):
        return False

    # Verify deletion by tring to retrieve instance info.
    request = service.instances().get(project=project,
                                      instance=instance_name)
    try:
        request.execute()
        return False
    except apiclient.errors.HttpError as e:
        return e.resp['status'] == '404'


def _wait_for_operation(request, op_poller):
    """Executes a request and waits for its operation to finish.

    Args:
        request: A apiclient.http.HttpRequest whose response is expected
            to be an Operation.
        op_poller: A function whose first argument is expected to be an
            Operation. When called on an operation, op_poller should
            poll the API and return an updated version of the same
            Operation.

    Returns:
        True if request executed without raising an HttpError, False
        otherwise
    """
    try:
        logging.debug('Executing synchronous request: %s', request.to_json())
        start_time = time.time()
        op = request.execute()
    except apiclient.errors.HttpError as e:
        logging.warn(str(e))
        return False

    poll_interval_secs = 1
    while op['status'] != 'DONE':
        time.sleep(poll_interval_secs)
        logging.debug('Polling Operation: %s', op)
        op = op_poller(op)

        # Exponential backoff up to maximum.
        poll_interval_secs = min(MAX_POLL_INTERVAL_SECS,
                                 2 * poll_interval_secs)
    duration = time.time() - start_time
    logging.debug('Operation completed in %s seconds: %s',
                  duration, request.to_json())

    return True


def _cloud_sql_op_poller_factory(service, project):
    """Creates a function that polls a Cloud SQL operation.

    The value returned by a call to this function can be provided as the
    op_poller argument to _wait_for_operation.

    Args:
        service: a apiclient.discovery.Resource object for interacting
            with the Cloud SQL API. This is usually the same object used
            to create the request that spawned the operation that will
            be waited on.
        project: a string specifying the GCP project in which the
            operation will be executing

    Returns:
        a function that can be used as the second argument to
        _wait_for_operation.
    """
    def op_poller(op):
        return (service.operations()
                .get(project=project, operation=op['name']).execute())
    return op_poller


def _gke_op_poller_factory(service, project, zone):
    """Creates a function that polls a GKE operation.

    The value returned by a call to this function can be provided as the
    op_poller argument to _wait_for_operation.

    Args:
        service: a apiclient.discovery.Resource object for interacting
            with the GKE API. This is usually the same object used to
            create the request that spawned the operation that will be
            waited on.
        project: a string specifying the GCP project in which the
            operation will be executing
        zone: a string specifying the GCE zone in which the operation
            will be running

    Returns:
        a function that can be used as the second argument to
        _wait_for_operation.
    """
    def op_poller(op):
        return (service.projects().zones().operations()
                .get(projectId=project, zone=zone, operationId=op['name'])
                .execute())
    return op_poller
