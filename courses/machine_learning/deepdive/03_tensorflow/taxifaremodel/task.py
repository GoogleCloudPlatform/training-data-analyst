import argparse
import json
import os

#import model # for python2
from . import model # for python3

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--train_data_path',
        help = 'GCS or local path to training data',
        required = True
    )
    parser.add_argument(
        '--train_steps',
        help = 'Steps to run the training job for (default: 1000)',
        type = int,
        default = 1000
    )
    parser.add_argument(
        '--eval_data_path',
        help = 'GCS or local path to evaluation data',
        required = True
    )
    parser.add_argument(
        '--output_dir',
        help = 'GCS location to write checkpoints and export models',
        required = True
    )
    parser.add_argument(
        '--job-dir',
        help='This is not used by our model, but it is required by gcloud',
    )
    args = parser.parse_args()

    # Run the training job
    model.train_and_evaluate(args.__dict__)