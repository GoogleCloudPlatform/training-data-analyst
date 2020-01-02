#!/usr/bin/env python
"""Create dataset for predicting lightning using Dataflow.

Copyright Google Inc.
2018 Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required
by applicable law or agreed to in writing, software distributed under the
License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.
"""
import argparse
import datetime
import logging
import os
import random
import shutil
import subprocess
import apache_beam as beam
import numpy as np
import tensorflow as tf

from ltgpred.goesutil import goesio
from ltgpred.trainer import boxdef as bd

def _generate_hours(starthour, endhour, startday, endday, year, is_train):
  for h in range(starthour, endhour+1):
    for d in range(startday, endday+1):
        data = {
          'hour': h,
          'day': d,
          'year': year
        }
        if hash(str(data)) % 10 < 7:
          if is_train:
            yield data
        else:
          if not is_train:
            yield data

def generate_hours(startdate: str, enddate: str, starthour: int, endhour: int, is_train: bool):
    """generates hours within the specified ranges for training or eval.

      Call this method twice, once with is_train=True and next with is_train=False
      Args:
        starthour (int): Start hour, in the range 0-23
        endhour (int): End hour (inclusive), in the range 0-23
        startdate (str): Year + Start Julian day, in the range 0-366 eg: 2018-109
        enddate (str): Year + End Julian day (inclusive), in the range 0-366:  2018-109
        is_train (bool): Generate training data or testing data?
      Yields:
        dict of {'hour': h, 'day': d, 'year': y}, one for each hour in the range
    """
    startyear = int(startdate[:4])
    endyear = int(enddate[:4])
    startday = int(startdate[5:])
    endday = int(enddate[5:])
    if endyear == startyear:
        yield from _generate_hours(starthour, endhour, startday, endday, startyear, is_train)
    else:
        # for startyear, go from startday to day#365
        # FIXME: leap years?
        yield from _generate_hours(starthour, endhour, startday, 365, startyear, is_train)
        for y in range(startyear+1, endyear):
            yield from _generate_hours(starthour, endhour, 1, 365, endyear, is_train)
        yield from _generate_hours(starthour, endhour, 1, endday, endyear, is_train)

def _int64_feature(value):
  """Wrapper for inserting int64 features into Example proto."""
  if not isinstance(value, list):
    value = [value]
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def _array_feature(value, min_value, max_value):
  """Wrapper for inserting ndarray float features into Example proto."""
  value = np.nan_to_num(value.flatten()) # nan, -inf, +inf to numbers
  value = np.clip(value, min_value, max_value) # clip to valid
  return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def _bytes_feature(value):
  """Wrapper for inserting bytes features into Example proto."""
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def create_training_examples(ref, ltg, ltgfcst, griddef, boxdef, samplingfrac):
  """Input function that yields dicts of CSV, tfrecord for each box in grid."""
  for example in boxdef.rawdata_input_fn(ref, ltg, griddef, ltgfcst):
    # write out all lightning patches, but only some of the non-lightning ones
    should_write = (example['has_ltg'] or
                    random.random() < samplingfrac)

    if should_write:
      # create a CSV line consisting of extracted features
      csv_data = [
          example['cy'],
          example['cx'],
          example['lat'],
          example['lon'],
          np.mean(example['ref_smallbox']),  # mean within subgrid
          np.max(example['ref_smallbox']),
          np.mean(example['ref_bigbox']),
          np.max(example['ref_bigbox']),
          np.mean(example['ltg_smallbox']),
          np.mean(example['ltg_bigbox']),
          example['has_ltg']
      ]
      csv_line = ','.join([str(v) for v in csv_data])

      # create a TF Record with the raw data
      tfexample = tf.train.Example(
          features=tf.train.Features(
              feature={
                  'cy': _int64_feature(example['cy']),
                  'cx': _int64_feature(example['cx']),
                  'lon': _array_feature(example['lon'], -180, 180),
                  'lat': _array_feature(example['lat'], -90, 90),
                  'ref': _array_feature(example['ref_bigbox'], 0, 1),
                  'ltg': _array_feature(example['ltg_bigbox'], 0, 1),
                  'has_ltg': _int64_feature(1 if example['has_ltg'] else 0)
              }))

      yield {
        'csvline': csv_line,
        'tfrecord': tfexample.SerializeToString(),
        'ref': example['ref_center'],
        'ltg' : example['ltg_center']
      }


def get_ir_blob_paths(hours_dict, max_per_hour=None):
  """Get IR records in this hour."""
  blob_paths = goesio.get_ir_blob_paths(hours_dict['year'], hours_dict['day'],
                                        hours_dict['hour'])
  if max_per_hour and len(blob_paths) > max_per_hour:
    blob_paths = blob_paths[:max_per_hour]
  for blob_path in blob_paths:
    yield blob_path


def add_time_stamp(ir_blob_path):
  epoch = datetime.utcfromtimestamp(0)
  timestamp = goesio.get_timestamp_from_filename(ir_blob_path)
  yield beam.window.TimestampedValue(ir_blob_path,
                                     (timestamp - epoch).total_seconds())


def create_record(ir_blob_path, griddef, boxdef, forecast_minutes,
                  ltg_validity_minutes, sampling_frac):
  # read IR image
  logging.info('Retrieving lightning for IR blob %s', ir_blob_path)
  ref = goesio.read_ir_data(ir_blob_path, griddef)
  ref = np.ma.filled(ref, 0) # mask -> 0

  # create "current" lightning image
  influence_km = 5
  irdt = goesio.get_timestamp_from_filename(ir_blob_path)
  ltg_blob_paths = goesio.get_ltg_blob_paths(
      irdt, timespan_minutes=ltg_validity_minutes)
  if ltg_blob_paths:
      ltg = goesio.create_ltg_grid(ltg_blob_paths, griddef, influence_km)

      # create "forecast" lightning image
      irdt = irdt + datetime.timedelta(minutes=forecast_minutes)
      ltg_blob_paths = goesio.get_ltg_blob_paths(
          irdt, timespan_minutes=ltg_validity_minutes)
      if ltg_blob_paths:
          ltgfcst = goesio.create_ltg_grid(ltg_blob_paths, griddef, influence_km)

          # create examples
          for example in create_training_examples(ref, ltg, ltgfcst,
                                                  griddef, boxdef,
                                                  sampling_frac):
            yield example

class MeanStddev(beam.CombineFn):
  def create_accumulator(self):
    return (0.0, 0.0, 0) # x, x^2, count

  def add_input(self, sum_count, input):
    (sum, sumsq, count) = sum_count
    return sum + input, sumsq + input*input, count + 1

  def merge_accumulators(self, accumulators):
    sums, sumsqs, counts = zip(*accumulators)
    return sum(sums), sum(sumsqs), sum(counts)

  def extract_output(self, sum_count):
    (sum, sumsq, count) = sum_count
    if count:
      mean = sum / count
      variance = (sumsq / count) - mean*mean
      # -ve value could happen due to rounding
      stddev = np.sqrt(variance) if variance > 0 else 0
      return {
        'mean': mean,
        'variance': variance,
        'stddev': stddev,
        'count': count
      }
    else:
      return {
        'mean': float('NaN'),
        'variance': float('NaN'),
        'stddev': float('NaN'),
        'count': 0
      }


def run_job(options):  # pylint: disable=redefined-outer-name
  """Run the job."""

  # for repeatability
  random.seed(13)

  # prediction box
  boxdef = bd.BoxDef(options['train_patch_radius'],
                     options['label_patch_radius'],
                     options['stride'])
  griddef = goesio.create_conus_griddef(options['latlonres'])
  # start the pipeline
  opts = beam.pipeline.PipelineOptions(flags=[], **options)
  with beam.Pipeline(options['runner'], options=opts) as p:
    for step in ['train', 'eval']:
      # create examples
      examples = (
          p
          | '{}_hours'.format(step) >> beam.Create(
              generate_hours(options['startday'], options['endday'],
                             options['starthour'], options['endhour'],
                             step == 'train'))
          | '{}_irblobs'.format(step) >>
          beam.FlatMap(lambda x: get_ir_blob_paths(x, options['max_per_hour']))
          | '{}_examples'.format(step) >>
          beam.FlatMap(
              lambda ir_blob_path:  # pylint: disable=g-long-lambda
              create_record(ir_blob_path, griddef, boxdef,
                            options['forecast_interval'],
                            options['lightning_validity'],
                            options['sampling_frac'])
          ))

      # shuffle the examples so that each small batch doesn't contain
      # highly correlated records
      examples = (examples
          | '{}_reshuffleA'.format(step) >> beam.Map(
              lambda t: (random.randint(1, 1000), t))
          | '{}_reshuffleB'.format(step) >> beam.GroupByKey()
          | '{}_reshuffleC'.format(step) >> beam.FlatMap(lambda t: t[1]))

      # write out center pixel statistics
      if step == 'train':
        _ = (examples
          | 'get_values' >> beam.FlatMap(
              lambda x : [(f, x[f]) for f in ['ref', 'ltg']])
          | 'compute_stats' >> beam.CombinePerKey(MeanStddev())
          | 'write_stats' >> beam.io.Write(beam.io.WriteToText(
              os.path.join(options['outdir'], 'stats'), num_shards=1))
        )


      # write out csv files
      _ = (
          examples
          | '{}_csvlines'.format(step) >> beam.Map(lambda x: x['csvline'])
          | '{}_writecsv'.format(step) >> beam.io.Write(
              beam.io.WriteToText(os.path.join(options['outdir'], 'csv', step))))

      # write out tfrecords
      _ = (
          examples
          | '{}_tfrecords'.format(step) >> beam.Map(lambda x: x['tfrecord'])
          | '{}_writetfr'.format(step) >> beam.io.tfrecordio.WriteToTFRecord(
              os.path.join(options['outdir'], 'tfrecord', step)))



if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Create training/eval files for lightning prediction')
  parser.add_argument(
      '--project',
      default='',
      help='Specify GCP project to bill to run on cloud')
  parser.add_argument(
      '--outdir', required=True, help='output dir. could be local or on GCS')
  parser.add_argument(
      '--train_patch_radius',
      type=int,
      default=32,
      help='learn from infrared, lightning within a 2Nx2N grid')
  parser.add_argument(
      '--label_patch_radius',
      type=int,
      default=2,
      help='learn to predict lightning within a 2Nx2N grid')
  parser.add_argument(
      '--stride', type=int, default=4, help='patch translation')
  parser.add_argument(
      '--latlonres',
      type=float,
      default=0.02,
      help='grid resolution in degrees lat/lon')
  parser.add_argument(
      '--startday',
      type=str,
      required=True,
      help='YEAR + start Julian day in year (Jan 1 = 1) e.g.  2018-108')
  parser.add_argument(
      '--endday',
      type=str,
      required=True,
      help='YEAR + end Julian day in year (Jan 1 = 1) e.g.  2019-108')
  parser.add_argument(
      '--starthour', type=int, default=0, help='start hour of day (0-23)')
  parser.add_argument(
      '--endhour', type=int, default=23, help='end hour of day (0-23)')
  parser.add_argument(
      '--max_per_hour',
      type=int,
      default=1,
      help='how many IR records per hour')
  parser.add_argument(
      '--forecast_interval',
      type=int,
      default=30,
      help='how far ahead to forecast (minutes)')
  parser.add_argument(
      '--lightning_validity',
      type=int,
      default=15,
      help='how long to retain a ltg flash (minutes)')
  parser.add_argument(
      '--sampling_frac',
      type=float,
      default=0.1,
      help='write out only this fraction of the no-lightning patches')

  # parse command-line args and add a few more
  logging.basicConfig(level=getattr(logging, 'INFO', None))
  options = parser.parse_args().__dict__
  outdir = options['outdir']
  options.update({
      'staging_location':
          os.path.join(outdir, 'tmp', 'staging'),
      'temp_location':
          os.path.join(outdir, 'tmp'),
      'job_name':
          'ltgpred-' + datetime.datetime.now().strftime('%y%m%d-%H%M%S'),
      'teardown_policy':
          'TEARDOWN_ALWAYS',
      'max_num_workers':
          20,
      'machine_type':
          'n1-standard-8',
      'setup_file':
          os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../setup.py'),
      'save_main_session':
          True,
      'sdk_location': # FIXME: remove this once 2.12 is released
          './local/beam/sdks/python/dist/apache-beam-2.12.0.tar.gz'
  })

  if not options['project']:
    print('Launching local job ... hang on')
    shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir)
    options['runner'] = 'DirectRunner'
  else:
    print('Launching Dataflow job {} ... hang on'.format(options['job_name']))
    try:
      subprocess.check_call('gsutil -m rm -r {}'.format(outdir).split())
    except:  # pylint: disable=bare-except
      pass
    options['runner'] = 'DataflowRunner'

  run_job(options)
