# Copyright 2017 Google Inc. All Rights Reserved.
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

from __future__ import print_function

import boto3
import json
import os
import urllib
import urllib2


print('Loading function')

s3 = boto3.client('s3')
endpoint_api_key = os.environ['ENDPOINT_API_KEY']
endpoint_url = "https://aeflex-endpoints.appspot.com/processmessage"

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object information from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    try:
        # Retrieve object metadata
        response = s3.head_object(Bucket=bucket, Key=object_key)
        # Generate pre-signed URL for object
        presigned_url = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': object_key}, ExpiresIn = 3600)
        data = {"inputMessage": {
                    "Bucket": bucket,
                    "ObjectKey": object_key,
                    "ContentType": response['ContentType'],
                    "ContentLength": response['ContentLength'],
                    "ETag": response['ETag'],
                    "PresignedUrl": presigned_url
            }
        }

        headers = {"Content-Type": "application/json",
                    "x-api-key": endpoint_api_key
        }
        # Invoke Cloud Endpoints API
        request = urllib2.Request(endpoint_url, data = json.dumps(data), headers = headers)
        response = urllib2.urlopen(request)
        
        print('Response text: {} \nResponse status: {}'.format(response.read(), response.getcode()))

        return response.getcode()
    except Exception as e:
        print(e)
        print('Error integrating lambda function with endpoint for the object {} in bucket {}'.format(object_key, bucket))
        raise e
