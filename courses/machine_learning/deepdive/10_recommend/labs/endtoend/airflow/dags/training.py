# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DAG definition for recserv model training."""

import airflow
from airflow import DAG

# Reference for all available airflow operators: 
# https://github.com/apache/incubator-airflow/tree/master/airflow/contrib/operators
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.operators.bigquery_to_gcs import BigQueryToCloudStorageOperator
from airflow.hooks.base_hook import BaseHook
# from airflow.contrib.operators.mlengine_operator import MLEngineTrainingOperator
# above mlengine_operator currently doesnt support custom MasterType so we import our own plugins:

# custom plugins
from airflow.operators.app_engine_admin_plugin import AppEngineVersionOperator
from airflow.operators.ml_engine_plugin import MLEngineTrainingOperator


import datetime

def _get_project_id():
  """Get project ID from default GCP connection."""

  extras = BaseHook.get_connection('google_cloud_default').extra_dejson
  key = 'extra__google_cloud_platform__project'
  if key in extras:
    project_id = extras[key]
  else:
    raise ('Must configure project_id in google_cloud_default '
           'connection from Airflow Console')
  return project_id

PROJECT_ID = _get_project_id()

# Data set constants, used in BigQuery tasks.  You can change these
# to conform to your data.

# TODO: Specify your BigQuery dataset name and table name
DATASET = ''
TABLE_NAME = ''
ARTICLE_CUSTOM_DIMENSION = '10'

# TODO: Confirm bucket name and region
# GCS bucket names and region, can also be changed.
BUCKET = 'gs://recserve_' + PROJECT_ID
REGION = 'us-east1'

# The code package name comes from the model code in the wals_ml_engine
# directory of the solution code base.
PACKAGE_URI = BUCKET + '/code/wals_ml_engine-0.1.tar.gz'
JOB_DIR = BUCKET + '/jobs'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'email': ['airflow@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 5,
    'retry_delay': datetime.timedelta(minutes=5)
}

# Default schedule interval using cronjob syntax - can be customized here
# or in the Airflow console.

# TODO: Specify a schedule interval in CRON syntax to run once a day at 2100 hours (9pm)
# Reference: https://airflow.apache.org/scheduler.html
schedule_interval = '' # example '00 XX 0 0 0'

# TODO: Title your DAG to be recommendations_training_v1
dag = DAG('', 
          default_args=default_args,
          schedule_interval=schedule_interval)

dag.doc_md = __doc__


#
#
# Task Definition
#
#

# BigQuery training data query

bql='''
#legacySql
SELECT
 fullVisitorId as clientId,
 ArticleID as contentId,
 (nextTime - hits.time) as timeOnPage,
FROM(
  SELECT
    fullVisitorId,
    hits.time,
    MAX(IF(hits.customDimensions.index={0},
           hits.customDimensions.value,NULL)) WITHIN hits AS ArticleID,
    LEAD(hits.time, 1) OVER (PARTITION BY fullVisitorId, visitNumber
                             ORDER BY hits.time ASC) as nextTime
  FROM [{1}.{2}.{3}]
  WHERE hits.type = "PAGE"
) HAVING timeOnPage is not null and contentId is not null;
'''

bql = bql.format(ARTICLE_CUSTOM_DIMENSION, PROJECT_ID, DATASET, TABLE_NAME)

# TODO: Complete the BigQueryOperator task to truncate the table if it already exists before writing
# Reference: https://airflow.apache.org/integration.html#bigqueryoperator
t1 = BigQuerySomething( # correct the operator name
    task_id='bq_rec_training_data',
    bql=bql,
    destination_dataset_table='%s.recommendation_events' % DATASET,
    write_disposition='WRITE_T_______', # specify to truncate on writes
    dag=dag)

# BigQuery training data export to GCS

# TODO: Fill in the missing operator name for task #2 which
# takes a BigQuery dataset and table as input and exports it to GCS as a CSV
training_file = BUCKET + '/data/recommendation_events.csv'
t2 = BigQueryToCloudSomethingSomething( # correct the name
    task_id='bq_export_op',
    source_project_dataset_table='%s.recommendation_events' % DATASET,
    destination_cloud_storage_uris=[training_file],
    export_format='CSV',
    dag=dag
)


# ML Engine training job

job_id = 'recserve_{0}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M'))
job_dir = BUCKET + '/jobs/' + job_id
output_dir = BUCKET
training_args = ['--job-dir', job_dir,
                 '--train-files', training_file,
                 '--output-dir', output_dir,
                 '--data-type', 'web_views',
                 '--use-optimized']

# TODO: Fill in the missing operator name for task #3 which will
# start a new training job to Cloud ML Engine
# Reference: https://airflow.apache.org/integration.html#cloud-ml-engine
# https://cloud.google.com/ml-engine/docs/tensorflow/machine-types
t3 = MLEngineSomethingSomething( # complete the name
    task_id='ml_engine_training_op',
    project_id=PROJECT_ID,
    job_id=job_id,
    package_uris=[PACKAGE_URI],
    training_python_module='trainer.task',
    training_args=training_args,
    region=REGION,
    scale_tier='CUSTOM',
    master_type='complex_model_m_gpu',
    dag=dag
)

# App Engine deploy new version

t4 = AppEngineVersionOperator(
    task_id='app_engine_deploy_version',
    project_id=PROJECT_ID,
    service_id='default',
    region=REGION,
    service_spec=None,
    dag=dag
)

# TODO: Be sure to set_upstream dependencies for all tasks
t2.set_upstream(t1)
t3.set_upstream(t2)
t4.set_upstream(t) # complete