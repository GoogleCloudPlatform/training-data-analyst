import traceback
import argparse
import json
import os
import tensorflow as tf

from . import model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Input Arguments
    parser.add_argument(
        '--train_data_path',
        help='GCS or local path to training data',
        required=True
    )
    parser.add_argument(
        '--train_batch_size',
        help='Batch size for training steps',
        type=int,
        default=16
    )
    parser.add_argument(
        '--eval_batch_size',
        help='Batch size for evaluation steps',
        type=int,
        default=16
    )
    parser.add_argument(
        '--eval_steps',
        help='Number of steps to run evalution for at each checkpoint',
        default=10,
        type=int
    )
    parser.add_argument(
        '--eval_data_path',
        help='GCS or local path to evaluation data',
        required=True
    )
    parser.add_argument(
        '--hidden_units',
        help='Hidden layer sizes for DNN, provide space-separated layers',
        type=str,
        default="128 32 4"
    )
    parser.add_argument(
        '--output_dir',
        help='GCS location to write checkpoints and export models',
        required=True
    )
    parser.add_argument(
        '--job-dir',
        help='this model ignores this field, but it is required by gcloud',
        default='junk'
    )

    args = parser.parse_args()
    arguments = args.__dict__

    output_dir = arguments['output_dir']

    # Append trial_id to path if we are doing hptuning
    # This code can be removed if you are not using hyperparameter tuning
    output_dir = os.path.join(
        output_dir,
        json.loads(
            os.environ.get('TF_CONFIG', '{}')
        ).get('task', {}).get('trial', '')
    )

    # Run the training job:
    try:
        model.train_and_evaluate(arguments)
    except:
        traceback.print_exc()
