import argparse
import json
import os
import sys

import tensorflow as tf

from . import model
from . import util


def _parse_arguments(argv):
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--epochs',
        help='The number of epochs to train',
        type=int, default=5)
    parser.add_argument(
        '--steps_per_epoch',
        help='The number of steps per epoch to train',
        type=int, default=500)
    parser.add_argument(
        '--train_path',
        help='The path to the training data',
        type=str, default="gs://cloud-ml-data/img/flower_photos/train_set.csv")
    parser.add_argument(
        '--eval_path',
        help='The path to the evaluation data',
        type=str, default="gs://cloud-ml-data/img/flower_photos/eval_set.csv")
    parser.add_argument(
        '--tpu_address',
        help='The path to the TPUs we will use in training',
        type=str, required=True)
    parser.add_argument(
        '--hub_path',
        help='The path to TF Hub module to use in GCS',
        type=str, required=True)
    parser.add_argument(
        '--job-dir',
        help='Directory where to save the given model',
        type=str, required=True)
    return parser.parse_known_args(argv)


def main():
    """Parses command line arguments and kicks off model training."""
    args = _parse_arguments(sys.argv[1:])[0]
    
    # TODO: define a TPU strategy
    resolver = tf.distribute.cluster_resolver.TPUClusterResolver(
        tpu=args.tpu_address)
    tf.config.experimental_connect_to_cluster(resolver)
    tf.tpu.experimental.initialize_tpu_system(resolver)
    strategy = tf.distribute.experimental.TPUStrategy(resolver)
    
    with strategy.scope():
        train_data = util.load_dataset(args.train_path)
        eval_data = util.load_dataset(args.eval_path, training=False)
        image_model = model.build_model(args.job_dir, args.hub_path)

    model_history = model.train_and_evaluate(
        image_model, args.epochs, args.steps_per_epoch,
        train_data, eval_data, args.job_dir)


if __name__ == '__main__':
    main()
