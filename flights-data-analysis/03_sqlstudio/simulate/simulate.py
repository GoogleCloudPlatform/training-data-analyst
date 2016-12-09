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

import time
import pytz
import logging
import argparse
import datetime
from google.cloud import pubsub
import google.cloud.bigquery as bq

TIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'

def publish(topics, allevents):
   for key in topics:  # 'departed', 'arrived', etc.
      topic = topics[key]
      events = allevents[key]
      with topic.batch() as batch:
         logging.info('Publishing {} {} events'.format(len(events), key))
         for event_data in events:
              batch.publish(event_data)

def notify(topics, rows, simStartTime, programStart, speedFactor):
   # sleep computation
   def compute_sleep_secs(notify_time):
        time_elapsed = (datetime.datetime.utcnow() - programStart).seconds
        sim_time_elapsed = (notify_time - simStartTime).seconds / speedFactor
        to_sleep_secs = sim_time_elapsed - time_elapsed
        return to_sleep_secs

   tonotify = {}
   for key in topics:
     tonotify[key] = list()

   for row in rows:
       event, notify_time, event_data = row
       tonotify[event].append(event_data)

       # how much time should we sleep?
       if compute_sleep_secs(notify_time) > 1:
          # notify the accumulated tonotify
          publish(topics, tonotify)
          for key in topics:
             tonotify[key] = list()

          # recompute sleep, since notification takes a while
          to_sleep_secs = compute_sleep_secs(notify_time)
          if to_sleep_secs > 0:
             logging.info('Sleeping {} seconds'.format(to_sleep_secs))
             time.sleep(to_sleep_secs)

   # left-over records; notify again
   publish(topics, tonotify)


if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Send simulated flight events to Cloud Pub/Sub')
   parser.add_argument('--startTime', help='Example: 2015-05-01 00:00:00 UTC', required=True)
   parser.add_argument('--endTime', help='Example: 2015-05-03 00:00:00 UTC', required=True)
   parser.add_argument('--speedFactor', help='Example: 60 implies 1 hour of data sent to Cloud Pub/Sub in 1 minute', required=True, type=float)

   # set up BigQuery bqclient
   logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
   args = parser.parse_args()
   bqclient = bq.Client()
   dataset = bqclient.dataset('flights')
   if not dataset.exists():
      logging.error('Did not find a dataset named <flights> in your project')
      exit(-1)
  
   # run the query to pull simulated events
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
   query = bqclient.run_sync_query(querystr.format(args.startTime,
                                                 args.endTime))
   query.use_legacy_sql = False # standard SQL
   query.timeout_ms = 2000
   query.max_results = 1000  # at a time
   query.run()

   # wait for query to complete and fetch first page of data
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

   # create one Pub/Sub notification topic for each type of event
   psclient = pubsub.Client()
   topics = {}
   for event_type in ['departed', 'arrived']:
       topics[event_type] = psclient.topic(event_type)
       if not topics[event_type].exists():
          topics[event_type].create()
   
   # notify about each row in the dataset
   programStartTime = datetime.datetime.utcnow() 
   simStartTime = datetime.datetime.strptime(args.startTime, TIME_FORMAT).replace(tzinfo=pytz.UTC)
   print 'Simulation start time is {}'.format(simStartTime)
   while True:
      notify(topics, rows, simStartTime, programStartTime, args.speedFactor)
      if token is None:
         break
      rows, total_count, token = query.fetch_data(page_token=token)
      
