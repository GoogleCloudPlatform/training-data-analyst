#!/usr/bin/env python3

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
from google.cloud import pubsub_v1 # Upgrading The Library
import google.cloud.bigquery as bq

TIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'
RFC3339_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S-00:00'

def publish(publisher, topics, allevents, notify_time):
   timestamp = notify_time.strftime(RFC3339_TIME_FORMAT)
   for key in topics:  # 'departed', 'arrived', etc.
      topic = topics[key]
      events = allevents[key]
      # the client automatically batches
      logging.info('Publishing {} {} till {}'.format(len(events), key, timestamp))
      for event_data in events:
          publisher.publish(topic, event_data.encode(), EventTimeStamp=timestamp)

def notify(publisher, topics, rows, simStartTime, programStart, speedFactor):
   # sleep computation
   def compute_sleep_secs(notify_time):
        time_elapsed = (datetime.datetime.utcnow() - programStart).total_seconds()
        sim_time_elapsed = (notify_time - simStartTime).total_seconds() / speedFactor
        to_sleep_secs = sim_time_elapsed - time_elapsed
        return to_sleep_secs

   tonotify = {}
   for key in topics:
     tonotify[key] = list()

   for row in rows:
       event, notify_time, event_data = row

       # how much time should we sleep?
       if compute_sleep_secs(notify_time) > 1:
          # notify the accumulated tonotify
          publish(publisher, topics, tonotify, notify_time)
          for key in topics:
             tonotify[key] = list()

          # recompute sleep, since notification takes a while
          to_sleep_secs = compute_sleep_secs(notify_time)
          if to_sleep_secs > 0:
             logging.info('Sleeping {} seconds'.format(to_sleep_secs))
             time.sleep(to_sleep_secs)
       tonotify[event].append(event_data)

   # left-over records; notify again
   publish(publisher, topics, tonotify, notify_time)


if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Send simulated flight events to Cloud Pub/Sub')
   parser.add_argument('--startTime', help='Example: 2015-05-01 00:00:00 UTC', required=True)
   parser.add_argument('--endTime', help='Example: 2015-05-03 00:00:00 UTC', required=True)
   parser.add_argument('--project', help='your project id, to create pubsub topic', required=True)
   parser.add_argument('--speedFactor', help='Example: 60 implies 1 hour of data sent to Cloud Pub/Sub in 1 minute', required=True, type=float)
   parser.add_argument('--jitter', help='type of jitter to add: None, uniform, exp  are the three options', default='None')

   # set up BigQuery bqclient
   logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
   args = parser.parse_args()
   bqclient = bq.Client(args.project)
   dataset =  bqclient.get_dataset( bqclient.dataset('flights') )  # throws exception on failure

   # jitter?
   if args.jitter == 'exp':
      jitter = 'CAST (-LN(RAND()*0.99 + 0.01)*30 + 90.5 AS INT64)'
   elif args.jitter == 'uniform':
      jitter = 'CAST(90.5 + RAND()*30 AS INT64)'
   else:
      jitter = '0'


   # run the query to pull simulated events
   querystr = """
SELECT
  EVENT,
  TIMESTAMP_ADD(NOTIFY_TIME, INTERVAL {} SECOND) AS NOTIFY_TIME,
  EVENT_DATA
FROM
  flights.simevents
WHERE
  NOTIFY_TIME >= TIMESTAMP('{}')
  AND NOTIFY_TIME < TIMESTAMP('{}')
ORDER BY
  NOTIFY_TIME ASC
"""
   rows = bqclient.query(querystr.format(jitter,
                                         args.startTime,
                                         args.endTime))

   # create one Pub/Sub notification topic for each type of event
   publisher = pubsub_v1.PublisherClient()
   topics = {}
   for event_type in ['wheelsoff', 'arrived', 'departed']:
       topics[event_type] = publisher.topic_path(args.project, event_type)
       try:
         # Getting the new topics from PubSub
          for topic in publisher.list_topics(request={"project": project_path}):
                print(topic)
       except:
         #Creating New topics
           publisher.create_topic(request={"name": topics[event_type]})

   # notify about each row in the dataset
   programStartTime = datetime.datetime.utcnow()
   simStartTime = datetime.datetime.strptime(args.startTime, TIME_FORMAT).replace(tzinfo=pytz.UTC)
   print('Simulation start time is {}'.format(simStartTime))
   notify(publisher, topics, rows, simStartTime, programStartTime, args.speedFactor)
