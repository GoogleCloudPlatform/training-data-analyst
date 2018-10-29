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
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.operators.bigquery_to_gcs import BigQueryToCloudStorageOperator
from airflow.hooks.base_hook import BaseHook
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
DATASET = 'GA360_test'
TABLE_NAME = 'ga_sessions_sample'
ARTICLE_CUSTOM_DIMENSION = '10'

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
schedule_interval = '00 21 * * *'

dag = DAG('recommendations_training_v1', default_args=default_args,
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

t1 = BigQueryOperator(
    task_id='bq_rec_training_data',
    bql=bql,
    destination_dataset_table='%s.recommendation_events' % DATASET,
    write_disposition='WRITE_TRUNCATE',
    dag=dag)

# BigQuery training data export to GCS

training_file = BUCKET + '/data/recommendation_events.csv'
t2 = BigQueryToCloudStorageOperator(
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

t3 = MLEngineTrainingOperator(
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

t2.set_upstream(t1)
t3.set_upstream(t2)
t4.set_upstream(t3)

