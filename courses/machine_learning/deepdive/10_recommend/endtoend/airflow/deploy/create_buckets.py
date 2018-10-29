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

"""Create buckets for 'Airflow on GKE' dags, logs and plugins."""

import yaml

from google.cloud import storage


def create_folder(gcs_bucket, folder):
  blob = gcs_bucket.blob(folder)
  blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')

with open('airflow/deploy/deployment-settings.yaml') as f:
  settings = yaml.load(f)
  bucket_uri = settings['id']

gcs_client = storage.Client()
bucket = gcs_client.get_bucket(bucket_uri)
create_folder(bucket, 'dags/')
create_folder(bucket, 'logs/')
create_folder(bucket, 'plugins/')
