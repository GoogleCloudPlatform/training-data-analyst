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

from __future__ import print_function
import apache_beam as beam
import csv

def addtimezone(lat, lon):
   try:
      import timezonefinder
      tf = timezonefinder.TimezoneFinder()
      return (lat, lon, tf.timezone_at(lng=float(lon), lat=float(lat)))
      #return (lat, lon, 'America/Los_Angeles') # FIXME
   except ValueError:
      return (lat, lon, 'TIMEZONE') # header

def as_utc(date, hhmm, tzone):
   try:
      if len(hhmm) > 0 and tzone is not None:
         import datetime, pytz
         loc_tz = pytz.timezone(tzone)
         loc_dt = loc_tz.localize(datetime.datetime.strptime(date,'%Y-%m-%d'), is_dst=False)
         # can't just parse hhmm because the data contains 2400 and the like ...
         loc_dt += datetime.timedelta(hours=int(hhmm[:2]), minutes=int(hhmm[2:]))
         utc_dt = loc_dt.astimezone(pytz.utc)
         return utc_dt.strftime('%Y-%m-%d %H:%M:%S'), loc_dt.utcoffset().total_seconds()
      else:
         return '',0 # empty string corresponds to canceled flights
   except ValueError as e:
      print('{} {} {}'.format(date, hhmm, tzone))
      raise e

def add_24h_if_before(arrtime, deptime):
   import datetime
   if len(arrtime) > 0 and len(deptime) > 0 and arrtime < deptime:
      adt = datetime.datetime.strptime(arrtime, '%Y-%m-%d %H:%M:%S')
      adt += datetime.timedelta(hours=24)
      return adt.strftime('%Y-%m-%d %H:%M:%S')
   else:
      return arrtime

def tz_correct(line, airport_timezones):
   fields = line.split(',')
   if fields[0] != 'FL_DATE' and len(fields) == 27:
      # convert all times to UTC
      dep_airport_id = fields[6]
      arr_airport_id = fields[10]
      dep_timezone = airport_timezones[dep_airport_id][2] 
      arr_timezone = airport_timezones[arr_airport_id][2]
      
      for f in [13, 14, 17]: #crsdeptime, deptime, wheelsoff
         fields[f], deptz = as_utc(fields[0], fields[f], dep_timezone)
      for f in [18, 20, 21]: #wheelson, crsarrtime, arrtime
         fields[f], arrtz = as_utc(fields[0], fields[f], arr_timezone)
      
      for f in [17, 18, 20, 21]:
         fields[f] = add_24h_if_before(fields[f], fields[14])

      fields.extend(airport_timezones[dep_airport_id])
      fields[-1] = str(deptz)
      fields.extend(airport_timezones[arr_airport_id])
      fields[-1] = str(arrtz)

      yield ','.join(fields)

if __name__ == '__main__':
   with beam.Pipeline('DirectRunner') as pipeline:

      airports = (pipeline
         | 'airports:read' >> beam.io.ReadFromText('airports.csv.gz')
         | 'airports:fields' >> beam.Map(lambda line: next(csv.reader([line])))
         | 'airports:tz' >> beam.Map(lambda fields: (fields[0], addtimezone(fields[21], fields[26])))
      )

      flights = (pipeline
         | 'flights:read' >> beam.io.ReadFromText('201501_part.csv')
         | 'flights:tzcorr' >> beam.FlatMap(tz_correct, beam.pvalue.AsDict(airports))
      )

      flights | beam.io.textio.WriteToText('all_flights')

      pipeline.run()
