# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Covertype Keras WideDeep Classifier.

See additional TFX example pipelines, including the Penguin Pipeline Kubeflow GCP example 
that this pipeline is based upon: https://github.com/tensorflow/tfx/blob/master/tfx/examples.

"""

import functools
import absl
import os
from typing import List, Text

import tensorflow as tf
import tensorflow_model_analysis as tfma
import tensorflow_transform as tft
from tensorflow_transform.tf_metadata import schema_utils
import kerastuner
from tensorflow_cloud import CloudTuner

from tfx.components.trainer.executor import TrainerFnArgs
from tfx.components.trainer.fn_args_utils import DataAccessor
from tfx.components.tuner.component import TunerFnResult
from tfx_bsl.tfxio import dataset_options

import features

# Model training constants.
EPOCHS = 1
TRAIN_BATCH_SIZE = 64
EVAL_BATCH_SIZE = 64
LOCAL_LOG_DIR = '/tmp/logs'


def _gzip_reader_fn(filenames):
  """Small utility returning a record reader that can read gzip'ed files."""
  return tf.data.TFRecordDataset(filenames, compression_type='GZIP')


def _get_serve_tf_examples_fn(model, tf_transform_output):
  """Returns a function that parses a serialized tf.Example and applies TFT."""

  model.tft_layer = tf_transform_output.transform_features_layer()

  @tf.function
  def serve_tf_examples_fn(serialized_tf_examples):
    """Returns the output to be used in the serving signature."""
    feature_spec = tf_transform_output.raw_feature_spec()
    feature_spec.pop(features.LABEL_KEY)
    parsed_features = tf.io.parse_example(serialized_tf_examples, feature_spec)

    transformed_features = model.tft_layer(parsed_features)

    return model(transformed_features)

  return serve_tf_examples_fn


def _input_fn(file_pattern: List[Text],
              data_accessor: DataAccessor,
              tf_transform_output: tft.TFTransformOutput,
              batch_size: int = 200) -> tf.data.Dataset:
  """Generates features and label for tuning/training.

  Args:
    file_pattern: List of paths or patterns of input tfrecord files.
    data_accessor: DataAccessor for converting input to RecordBatch.
    tf_transform_output: A TFTransformOutput.
    batch_size: representing the number of consecutive elements of returned
      dataset to combine in a single batch.

  Returns:
    A dataset that contains (features, indices) tuple where features is a
      dictionary of Tensors, and indices is a single Tensor of label indices.
  """
  dataset = data_accessor.tf_dataset_factory(
      file_pattern,
      dataset_options.TensorFlowDatasetOptions(
          batch_size=batch_size, label_key=features.transformed_name(features.LABEL_KEY)),
      tf_transform_output.transformed_metadata.schema)
    
  return dataset


def _get_hyperparameters() -> kerastuner.HyperParameters:
  """Returns hyperparameters for building Keras model.
  
  This function defines a conditional hyperparameter space and default values
  that are used to build the model.
  
  Args:
    None.
  Returns:
    A kerastuner HyperParameters object.
  """
  hp = kerastuner.HyperParameters()
  # Defines hyperparameter search space.
  hp.Float('learning_rate', min_value=1e-4, max_value=1e-2, sampling='log', default=1e-3)
  hp.Int('n_layers', 1, 2, default=1)
  # Based on n_layers, search for the optimal number of hidden units in each layer.
  with hp.conditional_scope('n_layers', 1):
        hp.Int('n_units_1', min_value=8, max_value=128, step=8, default=8)
  with hp.conditional_scope('n_layers', 2):
        hp.Int('n_units_1', min_value=8, max_value=128, step=8, default=8)
        hp.Int('n_units_2', min_value=8, max_value=128, step=8, default=8)

  return hp


def _build_keras_model(hparams: kerastuner.HyperParameters, 
                       tf_transform_output: tft.TFTransformOutput) -> tf.keras.Model:
  """Creates a Keras WideDeep Classifier model.
  Args:
    hparams: Holds HyperParameters for tuning.
    tf_transform_output: A TFTransformOutput.
  Returns:
    A keras Model.
  """
  # Defines deep feature columns and input layers.
  deep_columns = [
      tf.feature_column.numeric_column(
          key=features.transformed_name(key), 
          shape=())
      for key in features.NUMERIC_FEATURE_KEYS
  ]
  
  input_layers = {
      column.key: tf.keras.layers.Input(name=column.key, shape=(), dtype=tf.float32)
      for column in deep_columns
  }    

  # Defines wide feature columns and input layers.
  categorical_columns = [
      tf.feature_column.categorical_column_with_identity(
          key=features.transformed_name(key), 
          num_buckets=tf_transform_output.num_buckets_for_transformed_feature(features.transformed_name(key)), 
          default_value=0)
      for key in features.CATEGORICAL_FEATURE_KEYS
  ]

  wide_columns = [
      tf.feature_column.indicator_column(categorical_column)
      for categorical_column in categorical_columns
  ]
    
  input_layers.update({
      column.categorical_column.key: tf.keras.layers.Input(name=column.categorical_column.key, shape=(), dtype=tf.int32)
      for column in wide_columns
  })

  # Build Keras model using hparams.
  deep = tf.keras.layers.DenseFeatures(deep_columns)(input_layers)
  for n in range(int(hparams.get('n_layers'))):
    deep = tf.keras.layers.Dense(units=hparams.get('n_units_' + str(n + 1)))(deep)

  wide = tf.keras.layers.DenseFeatures(wide_columns)(input_layers)

  output = tf.keras.layers.Dense(features.NUM_CLASSES, activation='softmax')(
               tf.keras.layers.concatenate([deep, wide]))

  model = tf.keras.Model(input_layers, output)
  model.compile(
      loss='sparse_categorical_crossentropy',
      optimizer=tf.keras.optimizers.Adam(lr=hparams.get('learning_rate')),
      metrics=[tf.keras.metrics.SparseCategoricalAccuracy()])
  model.summary(print_fn=absl.logging.info)

  return model    


# TFX Tuner will call this function.
def tuner_fn(fn_args: TrainerFnArgs) -> TunerFnResult:
  """Build the tuner using CloudTuner (KerasTuner instance).
  Args:
    fn_args: Holds args used to train and tune the model as name/value pairs. See 
      https://www.tensorflow.org/tfx/api_docs/python/tfx/components/trainer/fn_args_utils/FnArgs.
  Returns:
    A namedtuple contains the following:
      - tuner: A BaseTuner that will be used for tuning.
      - fit_kwargs: Args to pass to tuner's run_trial function for fitting the
                    model , e.g., the training and validation dataset. Required
                    args depend on the above tuner's implementation.
  """
  transform_graph = tft.TFTransformOutput(fn_args.transform_graph_path)
  
  # Construct a build_keras_model_fn that just takes hyperparams from get_hyperparameters as input.
  build_keras_model_fn = functools.partial(
      _build_keras_model, tf_transform_output=transform_graph)  

  # CloudTuner is a subclass of kerastuner.Tuner which inherits from BaseTuner.   
  tuner = CloudTuner(
      build_keras_model_fn,
      project_id=fn_args.custom_config['ai_platform_training_args']['project'],
      region=fn_args.custom_config['ai_platform_training_args']['region'],      
      max_trials=30,
      hyperparameters=_get_hyperparameters(),
      objective=kerastuner.Objective('val_sparse_categorical_accuracy', 'max'),
      directory=fn_args.working_dir)
  
  train_dataset = _input_fn(
      fn_args.train_files,
      fn_args.data_accessor,
      transform_graph,
      batch_size=TRAIN_BATCH_SIZE)

  eval_dataset = _input_fn(
      fn_args.eval_files,
      fn_args.data_accessor,
      transform_graph,
      batch_size=EVAL_BATCH_SIZE)

  return TunerFnResult(
      tuner=tuner,
      fit_kwargs={
          'x': train_dataset,
          'validation_data': eval_dataset,
          'steps_per_epoch': fn_args.train_steps,
          'validation_steps': fn_args.eval_steps
      })


def _copy_tensorboard_logs(local_path: str, gcs_path: str):
    """Copies Tensorboard logs from a local dir to a GCS location.
    
    After training, batch copy Tensorboard logs locally to a GCS location. This can result
    in faster pipeline runtimes over streaming logs per batch to GCS that can get bottlenecked
    when streaming large volumes.
    
    Args:
      local_path: local filesystem directory uri.
      gcs_path: cloud filesystem directory uri.
    Returns:
      None.
    """
    pattern = '{}/*/events.out.tfevents.*'.format(local_path)
    local_files = tf.io.gfile.glob(pattern)
    gcs_log_files = [local_file.replace(local_path, gcs_path) for local_file in local_files]
    for local_file, gcs_file in zip(local_files, gcs_log_files):
        tf.io.gfile.copy(local_file, gcs_file)

        
# TFX Trainer will call this function.
def run_fn(fn_args: TrainerFnArgs):
  """Train the model based on given args.
  Args:
    fn_args: Holds args used to train and tune the model as name/value pairs. See 
      https://www.tensorflow.org/tfx/api_docs/python/tfx/components/trainer/fn_args_utils/FnArgs.
  """

  tf_transform_output = tft.TFTransformOutput(fn_args.transform_output)

  train_dataset = _input_fn(
      fn_args.train_files, 
      fn_args.data_accessor, 
      tf_transform_output, 
      TRAIN_BATCH_SIZE)

  eval_dataset = _input_fn(
      fn_args.eval_files, 
      fn_args.data_accessor,
      tf_transform_output, 
      EVAL_BATCH_SIZE)

  if fn_args.hyperparameters:
    hparams = kerastuner.HyperParameters.from_config(fn_args.hyperparameters)
  else:
    # This is a shown case when hyperparameters is decided and Tuner is removed
    # from the pipeline. User can also inline the hyperparameters directly in
    # _build_keras_model.
    hparams = _get_hyperparameters()
  absl.logging.info('HyperParameters for training: %s' % hparams.get_config())
  
  # Distribute training over multiple replicas on the same machine.
  mirrored_strategy = tf.distribute.MirroredStrategy()
  with mirrored_strategy.scope():
        model = _build_keras_model(
            hparams=hparams,
            tf_transform_output=tf_transform_output)       

  tensorboard_callback = tf.keras.callbacks.TensorBoard(
      log_dir=LOCAL_LOG_DIR, update_freq='batch')

  model.fit(
      train_dataset,
      epochs=EPOCHS,
      steps_per_epoch=fn_args.train_steps,
      validation_data=eval_dataset,
      validation_steps=fn_args.eval_steps,
      verbose=2,      
      callbacks=[tensorboard_callback])
    
  signatures = {
      'serving_default':
          _get_serve_tf_examples_fn(model,
                                    tf_transform_output).get_concrete_function(
                                        tf.TensorSpec(
                                            shape=[None],
                                            dtype=tf.string,
                                            name='examples')),
  }
  
  model.save(fn_args.serving_model_dir, save_format='tf', signatures=signatures)
  _copy_tensorboard_logs(LOCAL_LOG_DIR, fn_args.serving_model_dir + '/logs')
