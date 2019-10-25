# Copyright 2017 Google Inc.
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

import os
project_id = os.getenv('GCLOUD_PROJECT')
bucket_name = os.getenv('GCLOUD_BUCKET')

from google.cloud import storage

storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)

"""
Uploads a file to a given Cloud Storage bucket and returns the public url
to the new object.
"""
def upload_file(image_file, public):
    blob = bucket.blob(image_file.filename)

    blob.upload_from_string(
        image_file.read(),
        content_type=image_file.content_type)

    if public:
        blob.make_public()

    return blob.public_url
