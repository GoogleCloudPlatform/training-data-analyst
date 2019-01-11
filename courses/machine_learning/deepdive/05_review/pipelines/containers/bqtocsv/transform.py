#!/usr/bin/env python

import apache_beam as beam
import argparse
import datetime
import logging
import os


def to_csv(rowdict):
  # Pull columns from BQ and create a line
  import hashlib
  import copy
  CSV_COLUMNS = 'weight_pounds,is_male,mother_age,plurality,gestation_weeks'.split(',')

  # Create synthetic data where we assume that no ultrasound has been performed
  # and so we don't know sex of the baby. Let's assume that we can tell the difference
  # between single and multiple, but that the errors rates in determining exact number
  # is difficult in the absence of an ultrasound.
  no_ultrasound = copy.deepcopy(rowdict)
  w_ultrasound = copy.deepcopy(rowdict)

  no_ultrasound['is_male'] = 'Unknown'
  if rowdict['plurality'] > 1:
    no_ultrasound['plurality'] = 'Multiple(2+)'
  else:
    no_ultrasound['plurality'] = 'Single(1)'

  # Change the plurality column to strings
  w_ultrasound['plurality'] = ['Single(1)', 'Twins(2)', 'Triplets(3)', 'Quadruplets(4)', 'Quintuplets(5)'][
    rowdict['plurality'] - 1]

  # Write out two rows for each input row, one with ultrasound and one without
  for result in [no_ultrasound, w_ultrasound]:
    data = ','.join([str(result[k]) if k in result else 'None' for k in CSV_COLUMNS])
    key = hashlib.sha224(data).hexdigest()  # hash the columns to form a key
    yield str('{},{}'.format(data, key))


def preprocess(in_test_mode, PROJECT, BUCKET, start_year):
  import shutil, os, subprocess
  job_name = 'preprocess-babyweight-features' + '-' + datetime.datetime.now().strftime('%y%m%d-%H%M%S')

  if in_test_mode:
    print('Launching local job ... hang on')
    OUTPUT_DIR = './preproc'
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    os.makedirs(OUTPUT_DIR)
  else:
    print('Launching Dataflow job {} ... hang on'.format(job_name))
    if start_year == '2000':
      OUTPUT_DIR = 'gs://{0}/babyweight/preproc/'.format(BUCKET)
      try:
        subprocess.check_call(
           'gsutil -m rm -r {}'.format(OUTPUT_DIR).split())
      except:
        pass
       

  options = {
    'staging_location': os.path.join(OUTPUT_DIR, 'tmp', 'staging'),
    'temp_location': os.path.join(OUTPUT_DIR, 'tmp'),
    'job_name': job_name,
    'project': PROJECT,
    'teardown_policy': 'TEARDOWN_ALWAYS',
    'no_save_main_session': True
  }
  opts = beam.pipeline.PipelineOptions(flags=[], **options)
  if in_test_mode:
    RUNNER = 'DirectRunner'
  else:
    RUNNER = 'DataflowRunner'

  # run the pipeline
  with beam.Pipeline(RUNNER, options=opts) as p:
    query = """
      SELECT
        weight_pounds,
        is_male,
        mother_age,
        plurality,
        gestation_weeks,
        ABS(FARM_FINGERPRINT(CONCAT(CAST(YEAR AS STRING), CAST(month AS STRING)))) AS hashmonth
      FROM
        publicdata.samples.natality
      WHERE year >= {}
      AND weight_pounds > 0
      AND mother_age > 0
      AND plurality > 0
      AND gestation_weeks > 0
      AND month > 0
    """.format(start_year)

    if in_test_mode:
      query = query + ' LIMIT 100'

    for step in ['train', 'eval']:
      if step == 'train':
        selquery = 'SELECT * FROM ({}) WHERE MOD(ABS(hashmonth),4) < 3'.format(query)
      else:
        selquery = 'SELECT * FROM ({}) WHERE MOD(ABS(hashmonth),4) = 3'.format(query)

      (p
       | '{}_read'.format(step) >> beam.io.Read(beam.io.BigQuerySource(query=selquery, use_standard_sql=True))
       | '{}_csv'.format(step) >> beam.FlatMap(to_csv)
       | '{}_out'.format(step) >> beam.io.Write(beam.io.WriteToText(os.path.join(OUTPUT_DIR, '{}_{}.csv'.format(step, start_year))))
       )

  # the next step of pipeline will look for this file
  with open("/output.txt", "w") as output_file:
    output_file.write(BUCKET)
    print("Done!")


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--project',
                      type=str,
                      required=True,
                      help='The GCP project to run the dataflow job.')
  parser.add_argument('--bucket',
                      type=str,
                      required=True,
                      help='Bucket to store outputs.')
  parser.add_argument('--start_year',
                      type=str,
                      default='2000',
                      help='Year to start extracting data. If 2000, older data will be removed')
  parser.add_argument('--mode',
                      choices=['local', 'cloud'],
                      help='whether to run the job locally or in Cloud Dataflow.')

  args = parser.parse_args()

  preprocess(args.mode == 'local', args.project, args.bucket, args.start_year)
