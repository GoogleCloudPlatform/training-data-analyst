"""Generates the taxifare pipeline."""
from os import path

import kfp.compiler as compiler
import kfp.components as comp
import kfp.dsl as dsl
import kfp.gcp as gcp


HERE = path.abspath(path.dirname(__file__))
COMPONENT_DIR = path.join(HERE, "components")
BQ2GCS_YAML = path.join(COMPONENT_DIR, 'bq2gcs/component.yaml')
TRAINJOB_YAML = path.join(COMPONENT_DIR, 'trainjob/component.yaml')
PIPELINE_TAR = 'taxifare.tar.gz'


@dsl.pipeline(
    name='Taxifare',
    description='Train a ml model to predict the taxi fare in NY')
def pipeline(gcs_bucket_name='<bucket where data and model will be exported>'):

  bq2gcs_op = comp.load_component_from_file(BQ2GCS_YAML)
  trainjob_op = comp.load_component_from_file(TRAINJOB_YAML)

  bq2gcs = bq2gcs_op(
      input_bucket=gcs_bucket_name,
  ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  trainjob = trainjob_op(
      input_bucket=gcs_bucket_name,
  ).apply(gcp.use_gcp_secret('user-gcp-sa'))


  trainjob.after(bq2gcs)

if __name__ == '__main__':
  compiler.Compiler().compile(pipeline, PIPELINE_TAR, type_check=False)
