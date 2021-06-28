from typing import List, Optional
import logging

from tfx.extensions.google_cloud_big_query import BigQueryExampleGen
from tfx.components import Trainer


from google.cloud import aiplatform as vertex_ai


SCHEMA_FOLDER = 'schema'
TRANSFORM_MODULE_FILE = 'model/preprocessing.py'
TRAIN_MODULE_FILE = 'model/model.py'

def create_pipeline(pipeline_name: str, 
                    pipeline_root: str, 
                    query: str,
                    module_file: str, 
                    serving_model_dir: str,
                    beam_pipeline_args: Optional[List[str]],
                   ) -> tfx.dsl.Pipeline:
  """Creates a TFX pipeline."""

  # NEW: Query data in BigQuery as a data source.
  example_gen = BigQueryExampleGen(query=query)

  # Uses user-provided Python function that trains a model.
  trainer = Trainer(
      module_file=module_file,
      examples=example_gen.outputs['examples'],
      train_args=tfx.proto.TrainArgs(num_steps=100),
      eval_args=tfx.proto.EvalArgs(num_steps=5))

    return tfx.dsl.Pipeline(pipeline_name=pipeline_name,
                             pipeline_root=pipeline_root,
                             components=components,
                             enable_cache=enable_cache,
                             beam_pipeline_args=beam_pipeline_args)


def submit_pipeline(pipeline_definition_file):

    pipeline_client = AIPlatformClient(project_id=config.PROJECT, region=config.REGION)
    pipeline_client.create_run_from_job_spec(pipeline_definition_file)