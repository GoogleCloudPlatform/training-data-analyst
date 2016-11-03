# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Example Iris implementation to train on CloudML.

This sample reads the pre-processed data and its metadata features as generated
by the CloudML SDK and exports a model that can be used for serving.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import os
import sys

from . import util
import tensorflow as tf

import google.cloud.ml as ml

from tensorflow.contrib import metrics as metrics_lib
from tensorflow.contrib.learn.python.learn import learn_runner
from tensorflow.contrib.session_bundle import manifest_pb2

UNKNOWN_LABEL = 'UNKNOWN'

# Constants for the feature columns as present on the metadata. (see LandcoverFeatures in the notebook)
KEY_FEATURE_COLUMN = 'key'
TARGET_FEATURE_COLUMN = 'landcover'
REAL_VALUED_FEATURE_COLUMNS = 'inputbands'

# Constant to map the tf.Examples input placeholder.
EXAMPLES_PLACEHOLDER_KEY = 'examples'

# Constants for the output columns for prediction.
SCORES_OUTPUT_COLUMN = 'score'
KEY_OUTPUT_COLUMN = 'key'
TARGET_OUTPUT_COLUMN = 'target'
LABEL_OUTPUT_COLUMN = 'label'

# Constants for the exported input and output collections.
INPUTS_KEY = 'inputs'
OUTPUTS_KEY = 'outputs'


def get_placeholder_input_fn(metadata):
  """Wrap the create input placeholder function to provide the metadata."""

  def get_input_features():
    """Read the input features from the given placeholder."""
    examples = tf.placeholder(
        dtype=tf.string,
        shape=(None,),
        name='input_example')
    features = ml.features.FeatureMetadata.parse_features(metadata, examples)
    features[EXAMPLES_PLACEHOLDER_KEY] = examples
    # The target feature column is not used for prediction so return None.
    return features, None

  # Return a function to input the feaures into the model from a placeholder.
  return get_input_features


def get_reader_input_fn(metadata, data_paths, batch_size, shuffle):
  """Wrap the create input reader function to provide the runtime arguments."""

  def get_input_features():
    """Read the input features from the given data paths."""
    _, examples = util.read_examples(data_paths, batch_size, shuffle)
    features = ml.features.FeatureMetadata.parse_features(metadata, examples)
    # Retrieve the target feature column.
    target = features.pop(TARGET_FEATURE_COLUMN)
    return features, target

  # Return a function to input the feaures into the model from a data path.
  return get_input_features


def get_vocabulary(metadata_path):
  """Read a dictionary of iris labels to the metadata integer indexes."""
  metadata = ml.features.FeatureMetadata.get_metadata(metadata_path)
  return metadata.columns[TARGET_FEATURE_COLUMN]['vocab']


def get_export_signature_fn(metadata_path):
  """Wrap the create signature function to provide the metadata path."""

  def get_export_signature(examples, features, predictions):
    """Create an export signature with named input and output signatures."""
    iris_labels = get_vocabulary(metadata_path).keys()
    prediction = tf.argmax(predictions, 1)
    labels = tf.contrib.lookup.index_to_string(
        prediction, mapping=iris_labels, default_value=UNKNOWN_LABEL)

    target = tf.contrib.lookup.index_to_string(
        tf.squeeze(features[TARGET_FEATURE_COLUMN]), mapping=iris_labels,
        default_value=UNKNOWN_LABEL)

    outputs = {SCORES_OUTPUT_COLUMN: predictions.name,
               KEY_OUTPUT_COLUMN: tf.squeeze(features[KEY_FEATURE_COLUMN]).name,
               TARGET_OUTPUT_COLUMN: target.name,
               LABEL_OUTPUT_COLUMN: labels.name}

    inputs = {EXAMPLES_PLACEHOLDER_KEY: examples.name}

    tf.add_to_collection(INPUTS_KEY, json.dumps(inputs))
    tf.add_to_collection(OUTPUTS_KEY, json.dumps(outputs))

    input_signature = manifest_pb2.Signature()
    output_signature = manifest_pb2.Signature()

    for name, tensor_name in outputs.iteritems():
      output_signature.generic_signature.map[name].tensor_name = tensor_name

    for name, tensor_name in inputs.iteritems():
      input_signature.generic_signature.map[name].tensor_name = tensor_name

    # Return None for default classification signature.
    return None, {INPUTS_KEY: input_signature,
                  OUTPUTS_KEY: output_signature}

  # Return a function to create an export signature.
  return get_export_signature


def get_experiment_fn(args):
  """Wrap the create experiment function to provide the runtime arguments."""

  def get_experiment(output_dir):
    """Create a tf.contrib.learn.Experiment to be used by learn_runner."""
    config = tf.contrib.learn.RunConfig()
    # Write checkpoints more often for more granular evals, since the toy data
    # set is so small and simple. Most normal use cases should not set this and
    # just use the default (600).
    config.save_checkpoints_secs = 60

    # Load the metadata.
    metadata = ml.features.FeatureMetadata.get_metadata(
        args.metadata_path)

    # Specify the real valued feature colums that contain the measurements.
    feature_columns = [tf.contrib.layers.real_valued_column(
        metadata.features[REAL_VALUED_FEATURE_COLUMNS]['name'],
        dimension=metadata.features[REAL_VALUED_FEATURE_COLUMNS]['size'])]

    train_dir = os.path.join(output_dir, 'train')
    classifier = tf.contrib.learn.DNNClassifier(
        feature_columns=feature_columns,
        hidden_units=[args.layer1_size, args.layer2_size],
        n_classes=metadata.stats['labels'],
        config=config,
        model_dir=train_dir,
        optimizer=tf.train.AdamOptimizer(
            args.learning_rate, epsilon=args.epsilon))

    input_placeholder_for_prediction = get_placeholder_input_fn(
        metadata)

    # Export the last model to a predetermined location on GCS.
    export_monitor = util.ExportLastModelMonitor(
        output_dir=output_dir,
        final_model_location='model',  # Relative to the output_dir.
        additional_assets=[args.metadata_path],
        input_fn=input_placeholder_for_prediction,
        input_feature_key=EXAMPLES_PLACEHOLDER_KEY,
        signature_fn=get_export_signature_fn(args.metadata_path))

    input_reader_for_train = get_reader_input_fn(
        metadata, args.train_data_paths, args.batch_size, shuffle=True)
    input_reader_for_eval = get_reader_input_fn(
        metadata, args.eval_data_paths, args.eval_batch_size, shuffle=False)

    streaming_accuracy = metrics_lib.streaming_accuracy
    return tf.contrib.learn.Experiment(
        estimator=classifier,
        train_input_fn=input_reader_for_train,
        eval_input_fn=input_reader_for_eval,
        train_steps=args.max_steps,
        train_monitors=[export_monitor],
        min_eval_frequency=1000,
        eval_metrics={
            ('accuracy', 'classes'): streaming_accuracy,
            # Export the accuracy as a metric for hyperparameter tuning.
            ('training/hptuning/metric', 'classes'): streaming_accuracy
        })

  # Return a function to create an Experiment.
  return get_experiment


def parse_arguments(argv):
  """Parse the command line arguments."""
  parser = argparse.ArgumentParser()
  parser.add_argument('--train_data_paths', type=str, action='append')
  parser.add_argument('--eval_data_paths', type=str, action='append')
  parser.add_argument('--metadata_path', type=str)
  parser.add_argument('--output_path', type=str)
  parser.add_argument('--max_steps', type=int, default=5000)
  parser.add_argument('--layer1_size', type=int, default=20)
  parser.add_argument('--layer2_size', type=int, default=10)
  parser.add_argument('--learning_rate', type=float, default=0.01)
  parser.add_argument('--epsilon', type=float, default=0.0005)
  parser.add_argument('--batch_size', type=int, default=30)
  parser.add_argument('--eval_batch_size', type=int, default=30)
  return parser.parse_args(args=argv[1:])


def main(argv=None):
  """Runs a Tensorflow model on the Iris dataset."""
  args = parse_arguments(sys.argv if argv is None else argv)

  env = json.loads(os.environ.get('TF_CONFIG', '{}'))
  # First find out if there's a task value on the environment variable.
  # If there is none or it is empty define a default one.
  task_data = env.get('task') or {'type': 'master', 'index': 0}

  trial = task_data.get('trial')
  if trial is not None:
    output_dir = os.path.join(args.output_path, trial)
  else:
    output_dir = args.output_path

  learn_runner.run(
      experiment_fn=get_experiment_fn(args),
      output_dir=output_dir)


if __name__ == '__main__':
  tf.logging.set_verbosity(tf.logging.INFO)
  main()
