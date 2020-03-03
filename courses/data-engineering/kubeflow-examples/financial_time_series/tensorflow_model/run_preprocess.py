"""Module for running the data retrieval and preprocessing.

Scripts that performs all the steps to get the train and perform preprocessing.
"""
import logging
import argparse
import sys
import shutil
import os

#pylint: disable=no-name-in-module
from helpers import preprocess
from helpers import storage as storage_helper


def parse_arguments(argv):
  """Parse command line arguments
  Args:
      argv (list): list of command line arguments including program name
  Returns:
      The parsed arguments as returned by argparse.ArgumentParser
  """
  parser = argparse.ArgumentParser(description='Preprocessing')

  parser.add_argument('--bucket',
                      type=str,
                      help='GCS bucket where preprocessed data is saved',
                      default='<your-bucket-name>')

  parser.add_argument('--cutoff_year',
                      type=str,
                      help='Cutoff year for the stock data',
                      default='2010')

  parser.add_argument('--kfp',
                      dest='kfp',
                      action='store_true',
                      help='Kubeflow pipelines flag')

  args, _ = parser.parse_known_args(args=argv[1:])

  return args


def run_preprocess(argv=None):
  """Runs the retrieval and preprocessing of the data.

  Args:
    args: args that are passed when submitting the training

  Returns:

  """
  logging.info('starting preprocessing of data..')
  args = parse_arguments(sys.argv if argv is None else argv)
  tickers = ['snp', 'nyse', 'djia', 'nikkei', 'hangseng', 'ftse', 'dax', 'aord']
  closing_data = preprocess.load_data(tickers, args.cutoff_year)
  time_series = preprocess.preprocess_data(closing_data)
  logging.info('preprocessing of data complete..')

  logging.info('starting uploading of the preprocessed data on GCS..')
  temp_folder = 'data'
  if not os.path.exists(temp_folder):
    os.mkdir(temp_folder)
  file_path = os.path.join(temp_folder, 'data_{}.csv'.format(args.cutoff_year))
  time_series.to_csv(file_path, index=False)
  storage_helper.upload_to_storage(args.bucket, temp_folder)
  shutil.rmtree(temp_folder)
  if args.kfp:
    with open("/blob_path.txt", "w") as output_file:
      output_file.write(file_path)
  logging.info('upload of the preprocessed data on GCS completed..')


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  run_preprocess()
