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

def create_snapshots_one_by_one(outdir):
    import shutil,os
    import goes_to_jpeg as g2j
    shutil.rmtree(outdir, ignore_errors=True)
    os.mkdir(outdir)
    with open('MARIA.csv', 'r') as ifp:
     for line in ifp:
       jpgfile = g2j.goes_to_jpeg(line, None, outdir)
       break  # take out this  to process all the timestamps ...


def create_snapshots_on_cloud(bucket, project, runner):
   import datetime, os
   import apache_beam as beam
   import goes_to_jpeg as g2j

   input_file = 'maria/input/maria.csv'
   g2j.copy_togcs('MARIA.csv', bucket, input_file)

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
   with beam.Pipeline(runner, options=opts) as p:
      (p
        | 'lines' >> beam.io.ReadFromText(
                           'gs://{}/{}'.format(bucket, input_file))
        | 'to_jpg' >> beam.Map(lambda line: g2j.goes_to_jpeg(line, bucket, 'maria/images'))
      )
      p.run()

if __name__ == '__main__':
   import argparse
   parser = argparse.ArgumentParser(description='Plot the landfall of Hurricane Maria')
   parser.add_argument('--bucket', default='', help='Specify GCS bucket to run on cloud')
   parser.add_argument('--project', default='', help='Specify GCP project to bill')
   parser.add_argument('--outdir', default='image', help='output dir if local')
   
   opts = parser.parse_args()
   runner = 'DataflowRunner' # run on Cloud
   #runner = 'DirectRunner' # run Beam on local machine, but write outputs to cloud

   if len(opts.bucket) > 0:
      create_snapshots_on_cloud(opts.bucket, opts.project, runner)
   else:
      create_snapshots_one_by_one(opts.outdir)

