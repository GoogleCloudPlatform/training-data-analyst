#!/usr/bin/env python
# Copyright 2016 Google Inc.
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

# [START app]
import os
import logging
import transform

import flask
import google.cloud.storage as gcs

# [start config]
app = flask.Flask(__name__)
# Configure this environment variable via app.yaml
CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']
#
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
# [end config]

@app.route('/')
def welcome():
         return '<html><a href="ingest">ingest last week</a> earthquake data</html>'

@app.route('/ingest')
def ingest_last_week():
    try:
         # verify that this is a cron job request
         is_cron = flask.request.headers['X-Appengine-Cron']
         logging.info('Received cron request {}'.format(is_cron))

         # create png
         url = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.csv'
         outfile = 'earthquakes.png'
         status = 'scheduled ingest of {} to {}'.format(url, outfile)
         logging.info(status)
         transform.create_png(url, outfile)

         # upload to cloud storage
         client = gcs.Client()
         bucket = client.get_bucket(CLOUD_STORAGE_BUCKET)
         blob = gcs.Blob('earthquakes/earthquakes.png', bucket)
         blob.upload_from_filename(outfile)

         # change permissions
         blob.make_public()
         status = 'uploaded {} to {}'.format(outfile, blob.name)
         logging.info(status)

    except KeyError as e:
         status = '<html>Sorry, this capability is accessible only by the Cron service, but I got a KeyError for {} -- try invoking it from <a href="{}"> the GCP console / AppEngine / taskqueues </a></html>'.format(e, 'http://console.cloud.google.com/appengine/taskqueues?tab=CRON')
         logging.info('Rejected non-Cron request')

    return status

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
# [END app]
