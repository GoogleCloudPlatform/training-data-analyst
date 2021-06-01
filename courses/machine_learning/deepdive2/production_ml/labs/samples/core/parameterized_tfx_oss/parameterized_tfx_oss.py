#!/usr/bin/env python3
# Copyright 2019 Google LLC
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

import os

from typing import Text

import kfp
import tensorflow_model_analysis as tfma
from tfx.components.evaluator.component import Evaluator
from tfx.components.example_gen.csv_example_gen.component import CsvExampleGen
from tfx.components.example_validator.component import ExampleValidator
from tfx.components.pusher.component import Pusher
from tfx.components.schema_gen.component import SchemaGen
from tfx.components.statistics_gen.component import StatisticsGen
from tfx.components.trainer.component import Trainer
from tfx.components.transform.component import Transform
from tfx.orchestration import data_types
from tfx.orchestration import pipeline
from tfx.orchestration.kubeflow import kubeflow_dag_runner
from tfx.utils.dsl_utils import external_input
from tfx.proto import pusher_pb2
from tfx.proto import trainer_pb2

# Define pipeline params used for pipeline execution.
# Path to the module file, should be a GCS path,
# or a module file baked in the docker image used by the pipeline.
_taxi_module_file_param = data_types.RuntimeParameter(
    name='module-file',
    default='/tfx/src/tfx/examples/chicago_taxi_pipeline/taxi_utils.py',
    ptype=Text,
)

# Path to the CSV data file, under which their should be a data.csv file.
_data_root_param = data_types.RuntimeParameter(
    name='data-root',
    default='gs://ml-pipeline/sample-data/chicago-taxi/data',
    ptype=Text,
)

# Path of pipeline root, should be a GCS path.
pipeline_root = os.path.join(
    'gs://{{kfp-default-bucket}}', 'tfx_taxi_simple', kfp.dsl.RUN_ID_PLACEHOLDER
)


def _create_pipeline(
    pipeline_root: Text, csv_input_location: data_types.RuntimeParameter,
    taxi_module_file: data_types.RuntimeParameter, enable_cache: bool
):
  """Creates a simple Kubeflow-based Chicago Taxi TFX pipeline.

  Args:
    pipeline_root: The root of the pipeline output.
    csv_input_location: The location of the input data directory.
    taxi_module_file: The location of the module file for Transform/Trainer.
    enable_cache: Whether to enable cache or not.

  Returns:
    A logical TFX pipeline.Pipeline object.
  """
  examples = external_input(csv_input_location)

  example_gen = CsvExampleGen(input=examples)
  statistics_gen = StatisticsGen(examples=example_gen.outputs['examples'])
  infer_schema = SchemaGen(
      statistics=statistics_gen.outputs['statistics'],
      infer_feature_shape=False,
  )
  validate_stats = ExampleValidator(
      statistics=statistics_gen.outputs['statistics'],
      schema=infer_schema.outputs['schema'],
  )
  transform = Transform(
      examples=example_gen.outputs['examples'],
      schema=infer_schema.outputs['schema'],
      module_file=taxi_module_file,
  )
  trainer = Trainer(
      module_file=taxi_module_file,
      transformed_examples=transform.outputs['transformed_examples'],
      schema=infer_schema.outputs['schema'],
      transform_graph=transform.outputs['transform_graph'],
      train_args=trainer_pb2.TrainArgs(num_steps=10),
      eval_args=trainer_pb2.EvalArgs(num_steps=5),
  )
  # Set the TFMA config for Model Evaluation and Validation.
  eval_config = tfma.EvalConfig(
      model_specs=[
          # Using signature 'eval' implies the use of an EvalSavedModel. To use
          # a serving model remove the signature to defaults to 'serving_default'
          # and add a label_key.
          tfma.ModelSpec(signature_name='eval')
      ],
      metrics_specs=[
          tfma.MetricsSpec(
              # The metrics added here are in addition to those saved with the
              # model (assuming either a keras model or EvalSavedModel is used).
              # Any metrics added into the saved model (for example using
              # model.compile(..., metrics=[...]), etc) will be computed
              # automatically.
              metrics=[tfma.MetricConfig(class_name='ExampleCount')],
              # To add validation thresholds for metrics saved with the model,
              # add them keyed by metric name to the thresholds map.
              thresholds={
                  'binary_accuracy':
                      tfma.MetricThreshold(
                          value_threshold=tfma.GenericValueThreshold(
                              lower_bound={'value': 0.5}
                          ),
                          change_threshold=tfma.GenericChangeThreshold(
                              direction=tfma.MetricDirection.HIGHER_IS_BETTER,
                              absolute={'value': -1e-10}
                          )
                      )
              }
          )
      ],
      slicing_specs=[
          # An empty slice spec means the overall slice, i.e. the whole dataset.
          tfma.SlicingSpec(),
          # Data can be sliced along a feature column. In this case, data is
          # sliced along feature column trip_start_hour.
          tfma.SlicingSpec(feature_keys=['trip_start_hour'])
      ]
  )

  model_analyzer = Evaluator(
      examples=example_gen.outputs['examples'],
      model=trainer.outputs['model'],
      eval_config=eval_config,
  )

  pusher = Pusher(
      model=trainer.outputs['model'],
      model_blessing=model_analyzer.outputs['blessing'],
      push_destination=pusher_pb2.PushDestination(
          filesystem=pusher_pb2.PushDestination.Filesystem(
              base_directory=os.path.
              join(str(pipeline.ROOT_PARAMETER), 'model_serving')
          )
      ),
  )

  return pipeline.Pipeline(
      pipeline_name='parameterized_tfx_oss',
      pipeline_root=pipeline_root,
      components=[
          example_gen, statistics_gen, infer_schema, validate_stats, transform,
          trainer, model_analyzer, pusher
      ],
      enable_cache=enable_cache,
  )


if __name__ == '__main__':
  enable_cache = True
  pipeline = _create_pipeline(
      pipeline_root,
      _data_root_param,
      _taxi_module_file_param,
      enable_cache=enable_cache,
  )
  # Make sure the version of TFX image used is consistent with the version of
  # TFX SDK.
  config = kubeflow_dag_runner.KubeflowDagRunnerConfig(
      kubeflow_metadata_config=kubeflow_dag_runner.
      get_default_kubeflow_metadata_config(),
      tfx_image='gcr.io/tfx-oss-public/tfx:0.27.0',
  )
  kfp_runner = kubeflow_dag_runner.KubeflowDagRunner(
      output_filename=__file__ + '.yaml', config=config
  )

  kfp_runner.run(pipeline)
