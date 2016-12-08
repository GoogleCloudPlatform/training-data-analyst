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

import google.cloud.bigquery as bq
import argparse
import logging
import datetime
import time
import pytz

TIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'

def notify(rows, simStartTime, programStart, speedFactor):
   for row in rows:
       event, notify_time, event_data = row

       # how much time should we sleep?
       time_elapsed = (datetime.datetime.utcnow() - programStart).seconds
       sim_time_elapsed = (notify_time - simStartTime).seconds / speedFactor
       to_sleep_secs = sim_time_elapsed - time_elapsed
       if to_sleep_secs > 0:
          logging.info('Sleeping {} seconds'.format(to_sleep_secs))
          time.sleep(to_sleep_secs)

       # notify to Pub/Sub
       print event_data.split(',')[2:8]


if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Send simulated flight events to Cloud Pub/Sub')
   parser.add_argument('--startTime', help='Example: 2015-05-01 00:00:00 UTC', required=True)
   parser.add_argument('--endTime', help='Example: 2015-05-03 00:00:00 UTC', required=True)
   parser.add_argument('--speedFactor', help='Example: 60 implies 1 hour of data sent to Cloud Pub/Sub in 1 minute', required=True, type=float)

   # set up BigQuery client
   logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
   args = parser.parse_args()
   client = bq.Client()
   dataset = client.dataset('flights')
   if not dataset.exists():
      logging.error('Did not find a dataset named <flights> in your project')
      exit(-1)
  
   # set up the query to pull simulated events
   querystr = """\
SELECT
  EVENT,
  NOTIFY_TIME,
  EVENT_DATA
FROM
  `cloud-training-demos.flights.simevents`
WHERE
  NOTIFY_TIME >= TIMESTAMP('{}')
  AND NOTIFY_TIME < TIMESTAMP('{}')
ORDER BY
  NOTIFY_TIME ASC
"""
   query = client.run_sync_query(querystr.format(args.startTime,
                                                 args.endTime))
   query.use_legacy_sql = False # standard SQL
   query.timeout_ms = 2000
   query.max_results = 100  # at a time
   query.run()

   if query.complete:
      rows = query.rows
      token = query.page_token
   else:
      logging.error('Query timed out ... retrying ...')
      job = query.job
      job.reload()
      retry_count = 0
      while retry_count < 5 and job.state != u'DONE':
         time.sleep(1.5**retry_count)
         retry_count += 1
         logging.error('... retrying {}'.format(retry_count))
         job.reload()
      if job.state != u'DONE':
         logging.error('Job failed')
         logging.error(query.errors)
         exit(-1)
      rows, total_count, token = query.fetch_data()

   programStartTime = datetime.datetime.utcnow() 
   simStartTime = datetime.datetime.strptime(args.startTime, TIME_FORMAT).replace(tzinfo=pytz.UTC)
   print 'Simulation start time is {}'.format(simStartTime)
   while True:
      notify(rows, simStartTime, programStartTime, args.speedFactor)
      if token is None:
         break
      rows, total_count, token = query.fetch_data(page_token=token)
      
