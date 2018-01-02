#!/usr/bin/env python

"""
Copyright Google Inc. 2017
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

def create_snapshots_one_by_one(outdir, hurricane_file):
    import shutil,os
    import hurricanes.goes_to_jpeg as g2j
    shutil.rmtree(outdir, ignore_errors=True)
    os.mkdir(outdir)
    with open(hurricane_file, 'r') as ifp:
     for line in ifp:
       dt, lat, lon = g2j.parse_line(line)
       objectId = g2j.get_objectId_at(dt)
       outfilename = os.path.join(
                   outdir, 
                   'ir_{}{:02d}{:02d}{:02d}{:02d}.jpg'.format(
                       dt.year, dt.month, dt.day, dt.hour, dt.second))
       jpgfile = g2j.goes_to_jpeg(objectId, lat, lon, None, outfilename)
       break  # take out this  to process all the timestamps ...


def create_snapshots_on_cloud(bucket, project, runner, named_hurricane, hurricane_year):
   import datetime, os
   import apache_beam as beam
   import hurricanes.goes_to_jpeg as g2j

   query = """
SELECT
  latitude,
  longitude,
  iso_time,
  dist2land
FROM
  `bigquery-public-data.noaa_hurricanes.hurricanes`
WHERE
  name LIKE '%{0}%'
  AND season = '{1}'
   """.format(named_hurricane.upper(), hurricane_year)

   OUTPUT_DIR = 'gs://{}/maria/'.format(bucket)
   options = {
        'staging_location': os.path.join(OUTPUT_DIR, 'tmp', 'staging'),
        'temp_location': os.path.join(OUTPUT_DIR, 'tmp'),
        'job_name': 'maria-' + datetime.datetime.now().strftime('%y%m%d-%H%M%S'),
        'project': project,
        'max_num_workers': 12,
        'setup_file': './setup.py',
        'teardown_policy': 'TEARDOWN_ALWAYS',
        'no_save_main_session': True
   }
   opts = beam.pipeline.PipelineOptions(flags=[], **options)
   p = beam.Pipeline(runner, options=opts)
   (p
        | 'get_tracks' >> beam.io.Read(beam.io.BigQuerySource(query=query, use_standard_sql=True))
        | 'loc_at_time' >> beam.Map(lambda rowdict: (
                                     g2j.parse_timestamp(rowdict['iso_time']),
                                     rowdict['latitude'],
                                     rowdict['longitude']))
        | 'to_jpg' >> beam.Map(lambda (dt,lat,lon): 
            g2j.goes_to_jpeg(
                g2j.get_objectId_at(dt), 
                lat, lon, 
                bucket, 
                'maria/images/ir_{}{:02d}{:02d}{:02d}{:02d}.jpg'.format(
                       dt.year, dt.month, dt.day, dt.hour, dt.second)))
   )
   job = p.run()
   if runner == 'DirectRunner':
      job.wait_until_finish()

if __name__ == '__main__':
   import argparse, logging
   parser = argparse.ArgumentParser(description='Plot the landfall of Hurricane Maria')
   parser.add_argument('--bucket', default='', help='Specify GCS bucket to run on cloud')
   parser.add_argument('--project', default='', help='Specify GCP project to bill')
   parser.add_argument('--outdir', default='image', help='output dir if local')
   parser.add_argument('--hurricane', default='maria', help='name of hurricane')
   parser.add_argument('--year', default='2017', help='year of named hurricane')
   
   opts = parser.parse_args()
   runner = 'DataflowRunner' # run on Cloud
   #runner = 'DirectRunner' # run Beam on local machine, but write outputs to cloud
   logging.basicConfig(level=getattr(logging, 'INFO', None))

   if len(opts.bucket) > 0:
      logging.info('Running on cloud ...')
      create_snapshots_on_cloud(opts.bucket, opts.project, runner, opts.hurricane, opts.year)
   else:
      create_snapshots_one_by_one(opts.outdir, 'MARIA.csv')

