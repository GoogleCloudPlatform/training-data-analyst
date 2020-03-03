"""Module for running the training of the machine learning model.

Scripts that performs all the steps to train the ML model.
"""
import logging
import argparse
import sys


from run_preprocess import run_preprocess
from run_train import run_training
from run_deploy import run_deploy



def parse_arguments(argv):
  """Parse command line arguments
  Args:
      argv (list): list of command line arguments including program name
  Returns:
      The parsed arguments as returned by argparse.ArgumentParser
  """
  parser = argparse.ArgumentParser(description='Preprocess and Train')

  parser.add_argument('--cutoff_year',
                      type=str,
                      help='Cutoff year for the stock data',
                      default='2010')

  parser.add_argument('--bucket',
                      type=str,
                      help='GCS bucket to store data and ML models',
                      default='<your-bucket-name>')


  parser.add_argument('--model',
                      type=str,
                      help='model to be used for training',
                      default='DeepModel',
                      choices=['FlatModel', 'DeepModel'])

  parser.add_argument('--epochs',
                      type=int,
                      help='number of epochs to train',
                      default=30001)

  parser.add_argument('--tag',
                      type=str,
                      help='tag of the model',
                      default='v1')

  args, _ = parser.parse_known_args(args=argv[1:])

  return args

def run_preprocess_and_train(argv=None):
  """Runs the ML model pipeline.

  Args:
    args: args that are passed when submitting the training

  Returns:

  """
  args = parse_arguments(sys.argv if argv is None else argv)
  run_preprocess(sys.argv)
  sys.argv.append('--blob_path=data/data_{}.csv'.format(args.cutoff_year))
  run_training(sys.argv)
  run_deploy(sys.argv)


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  run_preprocess_and_train()
