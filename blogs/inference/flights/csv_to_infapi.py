#!/usr/bin/env python

"""
Copyright Google Inc. 2016
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import apache_beam as beam
import argparse

def thresh_delay(delaystr):
   delay = float(delaystr)
   if delay < -10:
        return 'Early'
   elif delay < 10:
        return 'Ontime'
   elif delay < 20:
        return 'Delayed'
   else:
        return 'Late'


def createJson(line):
   import json
   import uuid

   header = 'FL_DATE,UNIQUE_CARRIER,AIRLINE_ID,CARRIER,FL_NUM,ORIGIN_AIRPORT_ID,ORIGIN_AIRPORT_SEQ_ID,ORIGIN_CITY_MARKET_ID,ORIGIN,DEST_AIRPORT_ID,DEST_AIRPORT_SEQ_ID,DEST_CITY_MARKET_ID,DEST,CRS_DEP_TIME,DEP_TIME,DEP_DELAY,TAXI_OUT,WHEELS_OFF,WHEELS_ON,TAXI_IN,CRS_ARR_TIME,ARR_TIME,ARR_DELAY,CANCELLED,CANCELLATION_CODE,DIVERTED,DISTANCE,DEP_AIRPORT_LAT,DEP_AIRPORT_LON,DEP_AIRPORT_TZOFFSET,ARR_AIRPORT_LAT,ARR_AIRPORT_LON,ARR_AIRPORT_TZOFFSET'.split(',')

   featdict = {}
   fields = line.split(',')
   for name, value in zip(header, fields):
      featdict[name] = value

   rowid = uuid.uuid4().int & (1<<63) - 1 # make up a 64-bit rowid since this data doesn't have it
   for name in ['CARRIER', 'ORIGIN', 'DEST', 'DEP_DELAY', 
                'ARR_DELAY', 'CANCELLED']:
       try:
         value = featdict[name]
         if name == 'DEP_DELAY' or name == 'ARR_DELAY':
           value = thresh_delay(value)
         record = {
           'dataName': name,
           'dataValue': value,
           'groupId': str(rowid),  # int64 as a string
           'startTime': featdict['DEP_TIME'] + 'Z',
           # 'endTime': featdict['ARR_TIME'] + 'Z'  # do this for realtime analysis only
         }
         yield json.dumps(record).replace(' ', '')
       except:
         pass
   

if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Convert CSV of flights data to the JSON format expected by Inference API')
   parser.add_argument('--output_prefix', required=True, help='Output prefix')
   parser.add_argument('--input', required=True, help='Input pattern')

   options, pipeline_args = parser.parse_known_args()
   with beam.Pipeline(argv=pipeline_args) as p:
     (p
        | 'ReadLines' >> beam.io.ReadFromText(options.input)
        | 'Parse' >> beam.FlatMap(lambda line: createJson(line))
        | 'write' >> beam.io.WriteToText(options.output_prefix, num_shards=10)
     )

