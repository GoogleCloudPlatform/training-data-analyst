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
import ingest_flights

from flask import Flask
import google.cloud.storage as gcs

# [start config]
app = Flask(__name__)
# Configure this environment variable via app.yaml
CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']
# [end config]

@app.route('/')
def ingest_next_month():
         # next month
         bucket = CLOUD_STORAGE_BUCKET
         year, month = ingest_flights.next_month(bucket)
         logging.debug('Ingesting year={} month={}'.format(year, month))
   
         # ingest
         gcsfile = ingest_flights.ingest(year, month, bucket)

         # return page, and log
         if gcsfile is None:
            status = 'File for {}-{} not available yet ...'.format(year, month)
            logging.debug(status)
         else:
            status = 'Successfully ingested {}'.format(gcsfile)
            logging.info(status)
         return status

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]
