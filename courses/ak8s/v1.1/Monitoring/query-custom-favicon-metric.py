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
#
# Derived from Monitoring example from snippets.py 
#
# Package dependency:  pip install google-cloud-monitoring==0.31.1
#
# https://github.com/GoogleCloudPlatform/python-docs-samples

import argparse
import os
import pprint
import time

from google.cloud import monitoring_v3

def list_time_series(project_id):
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(project_id)
    interval = monitoring_v3.types.TimeInterval()
    now = time.time()
    interval.end_time.seconds = int(now)
    interval.end_time.nanos = int(
        (now - interval.end_time.seconds) * 10**9)
    interval.start_time.seconds = int(now - 15000)
    interval.start_time.nanos = interval.end_time.nanos
    try:
        results = client.list_time_series(
            project_name,
            'metric.type = "logging.googleapis.com/user/favicons_served"',
            interval,
            monitoring_v3.enums.ListTimeSeriesRequest.TimeSeriesView.FULL)
    except:
        return(0)
    total=0
    try:
        for result in results:
            total += 1
            for point in result.points:
                total += point.value.int64_value
                #print (point.value.int64_value)
        return(total)    
    except:
         return(0)   

def project_id():
    """Retreives the project id from the environment variable.

    Raises:
        MissingProjectIdError -- When not set.

    Returns:
        str -- the project name
    """
    project_id = (os.environ['GOOGLE_CLOUD_PROJECT'] or
                  os.environ['GCLOUD_PROJECT'])

    if not project_id:
        raise MissingProjectIdError(
            'Set the environment variable ' +
            'GCLOUD_PROJECT to your Google Cloud Project Id.')
    return project_id

if __name__ == '__main__':
    result=list_time_series(project_id())
    if result>1:
        print ("Favicon count: "+str(result))
