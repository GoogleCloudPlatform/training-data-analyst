# Copyright 2020 Google, LLC.
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

import requests
import json
import os

def handle_newfile(data, context):
    """Background Cloud Function to be triggered by Cloud Storage.
       This generic function calls the Cloud Run URL endpoint.

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    payload = {
        'bucket' : data['bucket'],
        'filename': data['name'] 
    }
    
    # Notes:    
    # (1) Ideally, we can simply invoke mlp_babyweight.finetune from here
    # However, kfp.Client() has dependencies on binaries that are not available in Cloud Functions
    # Hence, this workaround of putting mlp_babyweight.py in a Docker container and invoking it
    # via Cloud Run
    # (2) We could reduce the traffic to Cloud Run by checking filename pattern here
    # but for reusability and maintainability reasons, I'm keeping this
    # Cloud Function as a simple pass-through

    # receiving service url
    url = os.environ.get('DESTINATION_URL', "No DESTINATION_URL")
    print("Invoking Cloud Run at {} with {}".format(url, payload))     
      
    # See https://cloud.google.com/run/docs/authenticating/service-to-service
    metadata_server_token_url = 'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience='
    token_request_url = metadata_server_token_url + url
    token_request_headers = {'Metadata-Flavor': 'Google'}
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")

    # Provide the token in the request to the receiving service
    headers = {
        'Authorization': f'bearer {jwt}',
        'Content-Type':'application/json'
    }
    print("Headers = {}".format(headers))
    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    return (resp.status_code == requests.codes.ok)
