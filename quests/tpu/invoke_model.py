#!/usr/bin/env python

# Copyright 2018 Google Inc. All Rights Reserved.
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

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import base64, sys, json
import tensorflow as tf
import argparse

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--project',
      help='project where model is deployed',
      required=True)
  parser.add_argument(
      '--jpeg',
      help='file whose contents are to be sent to service',
      default='gs://cloud-ml-data/img/flower_photos/sunflowers/1022552002_2b93faf9e7_n.jpg'
      )
  args = parser.parse_args()

  with tf.gfile.FastGFile(args.jpeg, 'r') as ifp:
    credentials = GoogleCredentials.get_application_default()
    api = discovery.build('ml', 'v1', credentials=credentials,
               discoveryServiceUrl='https://storage.googleapis.com/cloud-ml/discovery/ml_v1_discovery.json')

    request_data = {'instances':
      [
         {"image_bytes": {"b64": base64.b64encode(ifp.read())}}
      ]
    }
    parent = 'projects/%s/models/%s/versions/%s' % (args.project, 'flowers', 'resnet')
    response = api.projects().predict(body=request_data, name=parent).execute()
    print("response={0}".format(response))
