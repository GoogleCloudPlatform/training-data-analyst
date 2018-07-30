"""Module to train sequence model.

Vectorizes training and validation texts into sequences and uses that for
training a sequence model - a sepCNN model. We use sequence model for text
classification when the ratio of number of samples to number of words per
sample for the given dataset is very large (>~15K).
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse

from . import model


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='./data',
                        help='input data directory')
    parser.add_argument(
        '--output_dir',
        help='GCS location to write checkpoints and export models',
        required=True
    )
    parser.add_argument(
        '--train_data_path',
        help='can be a local path or a GCS url (gs://...)',
        required=True
    )
    parser.add_argument(
        '--eval_data_path',
        help='can be a local path or a GCS url (gs://...)',
        required=True
    )
    parser.add_argument(
        '--embedding_path',
        help='can be a local path or a GCS url (gs://...)',
    )
    parser.add_argument(
        '--num_epochs',
        help='number of times to go through the data, default=10',
        default=10,
        type=float
    )
    parser.add_argument(
        '--batch_size',
        help='number of records to read during each training step, default=128',
        default=128,
        type=int
    )
    parser.add_argument(
        '--learning_rate',
        help='learning rate for gradient descent, default=.001',
        default=.001,
        type=float
    )

    args, _ = parser.parse_known_args()
    hparams = args.__dict__
    output_dir = hparams.pop('output_dir')

    model.train_and_evaluate(output_dir, hparams)
