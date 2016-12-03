#!/usr/bin/env python

import apache_beam as beam
import csv

def addtimezone(lat, lon):
   try:
      import timezonefinder
      tf = timezonefinder.TimezoneFinder()
      tz = tf.timezone_at(lng=float(lon), lat=float(lat))
      if tz is None:
         tz = 'UTC'
      return (lat, lon, tz)
   except ValueError:
      return (lat, lon, 'TIMEZONE') # header

if __name__ == '__main__':
   pipeline = beam.Pipeline('DirectPipelineRunner')

   airports = (pipeline 
      | beam.Read(beam.io.TextFileSource('airports.csv.gz'))
      | beam.Map(lambda line: next(csv.reader([line])))
      | beam.Map(lambda fields: (fields[0], addtimezone(fields[21], fields[26])))
   )

   airports | beam.Map(lambda (airport, data): '{},{}'.format(airport, ','.join(data)) )| beam.io.textio.WriteToText('airports_with_tz')

   pipeline.run()
