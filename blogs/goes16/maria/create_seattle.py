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

def create_snapshots_around_latlon(bucket, project, runner, lat, lon):
   import datetime, os
   import apache_beam as beam
   import hurricanes.goes_to_jpeg as g2j

   OUTPUT_DIR = 'gs://{}/realtime/'.format(bucket)
   options = {
        'staging_location': os.path.join(OUTPUT_DIR, 'tmp', 'staging'),
        'temp_location': os.path.join(OUTPUT_DIR, 'tmp'),
        'job_name': 'seattle-' + datetime.datetime.now().strftime('%y%m%d-%H%M%S'),
        'project': project,
        'max_num_workers': 3,
        'setup_file': './setup.py',
        'teardown_policy': 'TEARDOWN_ALWAYS',
        'no_save_main_session': True,
        'streaming': True
   }
   opts = beam.pipeline.PipelineOptions(flags=[], **options)
   p = beam.Pipeline(runner, options=opts)
   (p
        | 'events' >> beam.io.ReadStringsFromPubSub(
                           'projects/{}/topics/{}'.format(
                                   'gcp-public-data---goes-16',
                                   'gcp-public-data-goes-16'))
        | 'filter' >> beam.FlatMap(lambda message: g2j.only_infrared(message))
        | 'to_jpg' >> beam.Map(lambda objectid: 
            g2j.goes_to_jpeg(
                objectid, lat, lon, bucket,
                'goes/{}_{}/{}'.format( lat, lon, os.path.basename(objectid).replace('.nc','.jpg') ) 
                ))
   )
   job = p.run()
   if runner == 'DirectRunner':
      job.wait_until_finish()

if __name__ == '__main__':
   import argparse, logging
   parser = argparse.ArgumentParser(description='Plot images at a specific location in near-real-time')
   parser.add_argument('--bucket', required=True, help='Specify GCS bucket in which to save images')
   parser.add_argument('--project',required=True, help='Specify GCP project to bill')
   parser.add_argument('--lat', type=float, default=47.61, help='latitude of region center')
   parser.add_argument('--lon', type=float, default=-122.33, help='longitude of region center')
   
   opts = parser.parse_args()
   runner = 'DataflowRunner' # run on Cloud
   #runner = 'DirectRunner' # run Beam on local machine, but write outputs to cloud
   logging.basicConfig(level=getattr(logging, 'INFO', None))

   create_snapshots_around_latlon(opts.bucket, opts.project, runner, opts.lat, opts.lon)
