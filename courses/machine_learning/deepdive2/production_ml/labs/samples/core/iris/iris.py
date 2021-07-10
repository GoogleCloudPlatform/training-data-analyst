#!/usr/bin/env python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Iris flowers example using TFX. Based on https://github.com/tensorflow/tfx/blob/master/tfx/examples/iris/iris_pipeline_native_keras.py"""

import os
import kfp
from typing import Text

import absl
import tensorflow_model_analysis as tfma

from tfx.components import CsvExampleGen
from tfx.components import Evaluator
from tfx.components import ExampleValidator
from tfx.components import Pusher
from tfx.components import ResolverNode
from tfx.components import SchemaGen
from tfx.components import StatisticsGen
from tfx.components import Trainer
from tfx.components import Transform
from tfx.components.base import executor_spec
from tfx.components.trainer.executor import GenericExecutor
from tfx.dsl.experimental import latest_blessed_model_resolver
from tfx.orchestration import data_types
from tfx.orchestration import pipeline
from tfx.orchestration.kubeflow import kubeflow_dag_runner
from tfx.proto import trainer_pb2
from tfx.proto import pusher_pb2
from tfx.types import Channel
from tfx.types.standard_artifacts import Model
from tfx.types.standard_artifacts import ModelBlessing
from tfx.utils.dsl_utils import external_input

_pipeline_name = 'iris_native_keras'

# This example assumes that Iris flowers data is stored in GCS and the
# utility function is in iris_utils.py. Feel free to customize as needed.
_data_root_param = data_types.RuntimeParameter(
    name='data-root',
    default='gs://ml-pipeline/sample-data/iris/data',
    ptype=Text,
)

# Python module file to inject customized logic into the TFX components. The
# Transform and Trainer both require user-defined functions to run successfully.
# This file is fork from https://github.com/tensorflow/tfx/blob/master/tfx/examples/iris/iris_utils_native_keras.py
# and baked into the TFX image used in the pipeline.
_module_file_param = data_types.RuntimeParameter(
    name='module-file',
    default=
    '/tfx-src/tfx/examples/iris/iris_utils_native_keras.py',
    ptype=Text,
)

# Directory and data locations. This example assumes all of the flowers
# example code and metadata library is relative to a GCS path.
# Note: if one deployed KFP from GKE marketplace, it's possible to leverage
# the following magic placeholder to auto-populate the default GCS bucket
# associated with KFP deployment. Otherwise you'll need to replace it with your
# actual bucket name here or when creating a run.
_pipeline_root = os.path.join(
    'gs://{{kfp-default-bucket}}', 'tfx_iris', kfp.dsl.RUN_ID_PLACEHOLDER
)


def _create_pipeline(
    pipeline_name: Text, pipeline_root: Text
) -> pipeline.Pipeline:
  """Implements the Iris flowers pipeline with TFX."""
  examples = external_input(_data_root_param)

  # Brings data into the pipeline or otherwise joins/converts training data.
  example_gen = CsvExampleGen(input=examples)

  # Computes statistics over data for visualization and example validation.
  statistics_gen = StatisticsGen(examples=example_gen.outputs['examples'])

  # Generates schema based on statistics files.
  infer_schema = SchemaGen(
      statistics=statistics_gen.outputs['statistics'], infer_feature_shape=True
  )

  # Performs anomaly detection based on statistics and data schema.
  validate_stats = ExampleValidator(
      statistics=statistics_gen.outputs['statistics'],
      schema=infer_schema.outputs['schema']
  )

  # Performs transformations and feature engineering in training and serving.
  transform = Transform(
      examples=example_gen.outputs['examples'],
      schema=infer_schema.outputs['schema'],
      module_file=_module_file_param
  )

  # Uses user-provided Python function that implements a model using Keras.
  trainer = Trainer(
      module_file=_module_file_param,
      custom_executor_spec=executor_spec.ExecutorClassSpec(GenericExecutor),
      examples=transform.outputs['transformed_examples'],
      transform_graph=transform.outputs['transform_graph'],
      schema=infer_schema.outputs['schema'],
      train_args=trainer_pb2.TrainArgs(num_steps=100),
      eval_args=trainer_pb2.EvalArgs(num_steps=50)
  )

  # Get the latest blessed model for model validation.
  model_resolver = ResolverNode(
      instance_name='latest_blessed_model_resolver',
      resolver_class=latest_blessed_model_resolver.LatestBlessedModelResolver,
      model=Channel(type=Model),
      model_blessing=Channel(type=ModelBlessing)
  )

  # Uses TFMA to compute an evaluation statistics over features of a model and
  # perform quality validation of a candidate model (compared to a baseline).
  # Note: to compile this successfully you'll need TFMA at >= 0.21.5
  eval_config = tfma.EvalConfig(
      model_specs=[
          tfma.ModelSpec(name='candidate', label_key='variety'),
          tfma.ModelSpec(
              name='baseline', label_key='variety', is_baseline=True
          )
      ],
      slicing_specs=[
          tfma.SlicingSpec(),
          # Data can be sliced along a feature column. Required by TFMA visualization.
          tfma.SlicingSpec(feature_keys=['sepal_length'])],
      metrics_specs=[
          tfma.MetricsSpec(
              metrics=[
                  tfma.MetricConfig(
                      class_name='SparseCategoricalAccuracy',
                      threshold=tfma.config.MetricThreshold(
                          value_threshold=tfma.GenericValueThreshold(
                              lower_bound={'value': 0.9}
                          ),
                          change_threshold=tfma.GenericChangeThreshold(
                              direction=tfma.MetricDirection.HIGHER_IS_BETTER,
                              absolute={'value': -1e-10}
                          )
                      )
                  )
              ]
          )
      ]
  )

  # Uses TFMA to compute a evaluation statistics over features of a model.
  model_analyzer = Evaluator(
      examples=example_gen.outputs['examples'],
      model=trainer.outputs['model'],
      baseline_model=model_resolver.outputs['model'],
      # Change threshold will be ignored if there is no baseline (first run).
      eval_config=eval_config
  )

  # Checks whether the model passed the validation steps and pushes the model
  # to a file destination if check passed.
  pusher = Pusher(
      model=trainer.outputs['model'],
      model_blessing=model_analyzer.outputs['blessing'],
      push_destination=pusher_pb2.PushDestination(
          filesystem=pusher_pb2.PushDestination.Filesystem(
              base_directory=os.path.
              join(str(pipeline.ROOT_PARAMETER), 'model_serving')
          )
      )
  )

  return pipeline.Pipeline(
      pipeline_name=pipeline_name,
      pipeline_root=pipeline_root,
      components=[
          example_gen, statistics_gen, infer_schema, validate_stats, transform,
          trainer, model_resolver, model_analyzer, pusher
      ],
      enable_cache=True,
  )


if __name__ == '__main__':
  absl.logging.set_verbosity(absl.logging.INFO)
  # Make sure the version of TFX image used is consistent with the version of
  # TFX SDK. Here we use tfx:0.22.0 image.
  config = kubeflow_dag_runner.KubeflowDagRunnerConfig(
      kubeflow_metadata_config=kubeflow_dag_runner.
      get_default_kubeflow_metadata_config(),
      tfx_image='gcr.io/tfx-oss-public/tfx:0.22.0',
  )
  kfp_runner = kubeflow_dag_runner.KubeflowDagRunner(
      output_filename=__file__ + '.yaml', config=config
  )
  kfp_runner.run(
      _create_pipeline(
          pipeline_name=_pipeline_name, pipeline_root=_pipeline_root
      )
  )
