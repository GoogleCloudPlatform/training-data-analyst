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


import json
import kfp
from kfp import components
from kfp import dsl
import os
import subprocess

diagnose_me_op = components.load_component_from_url(
    'https://raw.githubusercontent.com/kubeflow/pipelines/566dddfdfc0a6a725b6e50ea85e73d8d5578bbb9/components/diagnostics/diagnose_me/component.yaml')

confusion_matrix_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/1.4.0/components/local/confusion_matrix/component.yaml')

roc_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/1.4.0/components/local/roc/component.yaml')

dataproc_create_cluster_op = components.load_component_from_url(
    'https://raw.githubusercontent.com/kubeflow/pipelines/1.4.0/components/gcp/dataproc/create_cluster/component.yaml')

dataproc_delete_cluster_op = components.load_component_from_url(
    'https://raw.githubusercontent.com/kubeflow/pipelines/1.4.0/components/gcp/dataproc/delete_cluster/component.yaml')

dataproc_submit_pyspark_op = components.load_component_from_url(
    'https://raw.githubusercontent.com/kubeflow/pipelines/1.4.0/components/gcp/dataproc/submit_pyspark_job/component.yaml'
)

dataproc_submit_spark_op = components.load_component_from_url(
    'https://raw.githubusercontent.com/kubeflow/pipelines/1.4.0/components/gcp/dataproc/submit_spark_job/component.yaml'
)

_PYSRC_PREFIX = 'gs://ml-pipeline/sample-pipeline/xgboost' # Common path to python src.

_XGBOOST_PKG = 'gs://ml-pipeline/sample-pipeline/xgboost/xgboost4j-example-0.8-SNAPSHOT-jar-with-dependencies.jar'

_TRAINER_MAIN_CLS = 'ml.dmlc.xgboost4j.scala.example.spark.XGBoostTrainer'

_PREDICTOR_MAIN_CLS = 'ml.dmlc.xgboost4j.scala.example.spark.XGBoostPredictor'


def delete_directory_from_gcs(dir_path):
  """Delete a GCS dir recursively. Ignore errors."""
  try:
    subprocess.call(['gsutil', '-m', 'rm', '-r', dir_path])
  except:
    pass


# ! Please do not forget to enable the Dataproc API in your cluster https://console.developers.google.com/apis/api/dataproc.googleapis.com/overview

# ================================================================
# The following classes should be provided by components provider.


def dataproc_analyze_op(
    project,
    region,
    cluster_name,
    schema,
    train_data,
    output):
  """Submit dataproc analyze as a pyspark job.

  :param project: GCP project ID.
  :param region: Which zone to run this analyze.
  :param cluster_name: Name of the cluster.
  :param schema: GCS path to the schema.
  :param train_data: GCS path to the training data.
  :param output: GCS path to store the output.
  """
  return dataproc_submit_pyspark_op(
      project_id=project,
      region=region,
      cluster_name=cluster_name,
      main_python_file_uri=os.path.join(_PYSRC_PREFIX, 'analyze_run.py'),
      args=['--output', str(output), '--train', str(train_data), '--schema', str(schema)]
  )


def dataproc_transform_op(
    project,
    region,
    cluster_name,
    train_data,
    eval_data,
    target,
    analysis,
    output
):
  """Submit dataproc transform as a pyspark job.

  :param project: GCP project ID.
  :param region: Which zone to run this analyze.
  :param cluster_name: Name of the cluster.
  :param train_data: GCS path to the training data.
  :param eval_data: GCS path of the eval csv file.
  :param target: Target column name.
  :param analysis: GCS path of the analysis results
  :param output: GCS path to use for output.
  """

  # Remove existing [output]/train and [output]/eval if they exist.
  delete_directory_from_gcs(os.path.join(output, 'train'))
  delete_directory_from_gcs(os.path.join(output, 'eval'))

  return dataproc_submit_pyspark_op(
      project_id=project,
      region=region,
      cluster_name=cluster_name,
      main_python_file_uri=os.path.join(_PYSRC_PREFIX,
                                        'transform_run.py'),
      args=[
        '--output',
        str(output),
        '--analysis',
        str(analysis),
        '--target',
        str(target),
        '--train',
        str(train_data),
        '--eval',
        str(eval_data)
      ])


def dataproc_train_op(
    project,
    region,
    cluster_name,
    train_data,
    eval_data,
    target,
    analysis,
    workers,
    rounds,
    output,
    is_classification=True
):

  if is_classification:
    config='gs://ml-pipeline/sample-data/xgboost-config/trainconfcla.json'
  else:
    config='gs://ml-pipeline/sample-data/xgboost-config/trainconfreg.json'

  return dataproc_submit_spark_op(
      project_id=project,
      region=region,
      cluster_name=cluster_name,
      main_class=_TRAINER_MAIN_CLS,
      spark_job=json.dumps({'jarFileUris': [_XGBOOST_PKG]}),
      args=json.dumps([
        str(config),
        str(rounds),
        str(workers),
        str(analysis),
        str(target),
        str(train_data),
        str(eval_data),
        str(output)
      ]))


def dataproc_predict_op(
    project,
    region,
    cluster_name,
    data,
    model,
    target,
    analysis,
    output
):

  return dataproc_submit_spark_op(
      project_id=project,
      region=region,
      cluster_name=cluster_name,
      main_class=_PREDICTOR_MAIN_CLS,
      spark_job=json.dumps({'jarFileUris': [_XGBOOST_PKG]}),
      args=json.dumps([
        str(model),
        str(data),
        str(analysis),
        str(target),
        str(output)
      ]))

# =======================================================================

@dsl.pipeline(
    name='XGBoost Trainer',
    description='A trainer that does end-to-end distributed training for XGBoost models.'
)
def xgb_train_pipeline(
    output='gs://{{kfp-default-bucket}}',
    project='{{kfp-project-id}}',
    diagnostic_mode='HALT_ON_ERROR',
    rounds=5,
):
    output_template = str(output) + '/' + dsl.RUN_ID_PLACEHOLDER + '/data'
    region='us-central1'
    workers=2
    quota_check=[{'region':region,'metric':'CPUS','quota_needed':12.0}]
    train_data='gs://ml-pipeline/sample-data/sfpd/train.csv'
    eval_data='gs://ml-pipeline/sample-data/sfpd/eval.csv'
    schema='gs://ml-pipeline/sample-data/sfpd/schema.json'
    true_label='ACTION'
    target='resolution'
    required_apis='dataproc.googleapis.com'
    cluster_name='xgb-%s' % dsl.RUN_ID_PLACEHOLDER

    # Current GCP pyspark/spark op do not provide outputs as return values, instead,
    # we need to use strings to pass the uri around.
    analyze_output = output_template
    transform_output_train = os.path.join(output_template, 'train', 'part-*')
    transform_output_eval = os.path.join(output_template, 'eval', 'part-*')
    train_output = os.path.join(output_template, 'train_output')
    predict_output = os.path.join(output_template, 'predict_output')
    
    _diagnose_me_op = diagnose_me_op(
        bucket=output,
        execution_mode=diagnostic_mode,
        project_id=project, 
        target_apis=required_apis,
        quota_check=quota_check)
    
    with dsl.ExitHandler(exit_op=dataproc_delete_cluster_op(
        project_id=project,
        region=region,
        name=cluster_name
    )):
        _create_cluster_op = dataproc_create_cluster_op(
            project_id=project,
            region=region,
            name=cluster_name,
            initialization_actions=[
              os.path.join(_PYSRC_PREFIX,
                           'initialization_actions.sh'),
            ],
            image_version='1.5'
        ).after(_diagnose_me_op)

        _analyze_op = dataproc_analyze_op(
            project=project,
            region=region,
            cluster_name=cluster_name,
            schema=schema,
            train_data=train_data,
            output=output_template
        ).after(_create_cluster_op).set_display_name('Analyzer')

        _transform_op = dataproc_transform_op(
            project=project,
            region=region,
            cluster_name=cluster_name,
            train_data=train_data,
            eval_data=eval_data,
            target=target,
            analysis=analyze_output,
            output=output_template
        ).after(_analyze_op).set_display_name('Transformer')

        _train_op = dataproc_train_op(
            project=project,
            region=region,
            cluster_name=cluster_name,
            train_data=transform_output_train,
            eval_data=transform_output_eval,
            target=target,
            analysis=analyze_output,
            workers=workers,
            rounds=rounds,
            output=train_output
        ).after(_transform_op).set_display_name('Trainer')

        _predict_op = dataproc_predict_op(
            project=project,
            region=region,
            cluster_name=cluster_name,
            data=transform_output_eval,
            model=train_output,
            target=target,
            analysis=analyze_output,
            output=predict_output
        ).after(_train_op).set_display_name('Predictor')

        _cm_op = confusion_matrix_op(
            predictions=os.path.join(predict_output, 'part-*.csv'),
            output_dir=output_template
        ).after(_predict_op)

        _roc_op = roc_op(
            predictions_dir=os.path.join(predict_output, 'part-*.csv'),
            true_class=true_label,
            true_score_column=true_label,
            output_dir=output_template
        ).after(_predict_op)

if __name__ == '__main__':
    kfp.compiler.Compiler().compile(xgb_train_pipeline, __file__ + '.yaml')
