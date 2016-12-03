#!/usr/bin/env python

import apache_beam as beam
import csv

if __name__ == '__main__':
   pipeline = beam.Pipeline('DirectPipelineRunner')

   airports = (pipeline 
      | beam.Read(beam.io.TextFileSource('airports.csv.gz'))
      | beam.Map(lambda line: next(csv.reader([line])))
      | beam.Map(lambda fields: (fields[0], (fields[21], fields[26])))
   )

   airports | beam.Map(lambda (airport, data): '{},{}'.format(airport, ','.join(data)) )| beam.io.textio.WriteToText('extracted_airports')

   pipeline.run()
