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

"""DAG definition for taxifare automated pipeline."""

import airflow
from airflow import DAG

# Reference for all available airflow operators: 
# https://github.com/apache/incubator-airflow/tree/master/airflow/contrib/operators
from airflow.contrib.operators.bigquery_check_operator import BigQueryCheckOperator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.operators.bigquery_to_gcs import BigQueryToCloudStorageOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.hooks.base_hook import BaseHook

from airflow.contrib.operators.mlengine_operator import MLEngineTrainingOperator, MLEngineModelOperator, MLEngineVersionOperator
from airflow.models import TaskInstance

import datetime
import logging

def _get_project_id():
  """Get project ID from default GCP connection."""

  extras = BaseHook.get_connection("google_cloud_default").extra_dejson
  key = "extra__google_cloud_platform__project"
  if key in extras:
    project_id = extras[key]
  else:
    raise ("Must configure project_id in google_cloud_default "
           "connection from Airflow Console")
  return project_id

PROJECT_ID = _get_project_id()

# Data set constants, used in BigQuery tasks.    You can change these
# to conform to your data.

# Specify your source BigQuery project, dataset, and table names
SOURCE_BQ_PROJECT = "nyc-tlc"
SOURCE_DATASET_TABLE_NAMES = "yellow.trips,green.trips_2014,green.trips_2015".split(",")

# Specify your destination BigQuery dataset
DESTINATION_DATASET = "taxifare"

# GCS bucket names and region, can also be changed.
BUCKET = "gs://" + PROJECT_ID + "-bucket"
REGION = "us-east1"

# # The code package name comes from the model code in the wals_ml_engine
# # directory of the solution code base.
PACKAGE_URI = BUCKET + "/taxifare/code/taxifare-0.1.tar.gz"
JOB_DIR = BUCKET + "/jobs"

default_args = {
  "owner": "airflow",
  "depends_on_past": False,
  "start_date": airflow.utils.dates.days_ago(2),
  "email": ["airflow@example.com"],
  "email_on_failure": True,
  "email_on_retry": False,
  "retries": 5,
  "retry_delay": datetime.timedelta(minutes=5)
}

# Default schedule interval using cronjob syntax - can be customized here
# or in the Airflow console.

# Specify a schedule interval in CRON syntax to run once a day at 2100 hours (9pm)
# Reference: https://airflow.apache.org/scheduler.html
schedule_interval = "00 21 * * *"

# Title your DAG
dag = DAG(
  "taxifare_multi", 
  default_args=default_args,
  schedule_interval=None
)

dag.doc_md = __doc__


#
#
# Task Definition
#
#

for model in SOURCE_DATASET_TABLE_NAMES:
  # BigQuery data query
  bql="""
  SELECT
    (tolls_amount + fare_amount) AS fare_amount,
    EXTRACT(DAYOFWEEK FROM pickup_datetime) * 1.0 AS dayofweek,
    EXTRACT(HOUR FROM pickup_datetime) * 1.0 AS hourofday,
    pickup_longitude AS pickuplon,
    pickup_latitude AS pickuplat,
    dropoff_longitude AS dropofflon,
    dropoff_latitude AS dropofflat,
    passenger_count*1.0 AS passengers,
    CONCAT(CAST(pickup_datetime AS STRING), CAST(pickup_longitude AS STRING), CAST(pickup_latitude AS STRING), CAST(dropoff_latitude AS STRING), CAST(dropoff_longitude AS STRING)) AS key
  FROM
    `{0}.{1}`
  WHERE
    trip_distance > 0
    AND fare_amount >= 2.5
    AND pickup_longitude > -78
    AND pickup_longitude < -70
    AND dropoff_longitude > -78
    AND dropoff_longitude < -70
    AND pickup_latitude > 37
    AND pickup_latitude < 45
    AND dropoff_latitude > 37
    AND dropoff_latitude < 45
    AND passenger_count > 0
    AND rand() < 0.00001
  """

  bql = bql.format(SOURCE_BQ_PROJECT, model)

  bql_train = "SELECT * EXCEPT (key) FROM({0}) WHERE ABS(MOD(FARM_FINGERPRINT(key), 5)) < 4".format(bql)
  bql_eval = "SELECT * EXCEPT (key) FROM({0}) WHERE ABS(MOD(FARM_FINGERPRINT(key), 5)) = 4".format(bql)

  # Complete the BigQueryOperator task to truncate the table if it already exists before writing
  # Reference: https://airflow.apache.org/integration.html#bigqueryoperator
  bq_train_data_op = BigQueryOperator(
    task_id="bq_train_data_{}_task".format(model.replace(".","_")),
    bql=bql_train,
    destination_dataset_table="{}.{}_train_data".format(DESTINATION_DATASET, model.replace(".","_")),
    write_disposition="WRITE_TRUNCATE", # specify to truncate on writes
    use_legacy_sql=False,
    dag=dag
  )

  bq_eval_data_op = BigQueryOperator(
    task_id="bq_eval_data_{}_task".format(model.replace(".","_")),
    bql=bql_eval,
    destination_dataset_table="{}.{}_eval_data".format(DESTINATION_DATASET, model.replace(".","_")),
    write_disposition="WRITE_TRUNCATE", # specify to truncate on writes
    use_legacy_sql=False,
    dag=dag
  )

  sql = """
  SELECT
    COUNT(*)
  FROM
    [{0}:{1}.{2}]
  """

  # Check to make sure that the data tables won"t be empty
  bq_check_train_data_op = BigQueryCheckOperator(
    task_id="bq_check_train_data_{}_task".format(model.replace(".","_")),
    sql=sql.format(PROJECT_ID, DESTINATION_DATASET, model.replace(".","_") + "_train_data"),
    dag=dag
  )

  bq_check_eval_data_op = BigQueryCheckOperator(
    task_id="bq_check_eval_data_{}_task".format(model.replace(".","_")),
    sql=sql.format(PROJECT_ID, DESTINATION_DATASET, model.replace(".","_") + "_eval_data"),
    dag=dag
  )

  # BigQuery training data export to GCS
  bash_remove_old_data_op = BashOperator(
    task_id="bash_remove_old_data_{}_task".format(model.replace(".","_")),
    bash_command="if gsutil ls {0}/taxifare/data/{1} 2> /dev/null; then gsutil -m rm -rf {0}/taxifare/data/{1}/*; else true; fi".format(BUCKET, model.replace(".","_")),
    dag=dag
  )

  # Takes a BigQuery dataset and table as input and exports it to GCS as a CSV
  train_files = BUCKET + "/taxifare/data/"

  bq_export_gcs_train_csv_op = BigQueryToCloudStorageOperator(
    task_id="bq_export_gcs_train_csv_{}_task".format(model.replace(".","_")),
    source_project_dataset_table="{}.{}_train_data".format(DESTINATION_DATASET, model.replace(".","_")),
    destination_cloud_storage_uris=[train_files + "{}/train-*.csv".format(model.replace(".","_"))],
    export_format="CSV",
    print_header=False,
    dag=dag
  )

  eval_files = BUCKET + "/taxifare/data/"

  bq_export_gcs_eval_csv_op = BigQueryToCloudStorageOperator(
    task_id="bq_export_gcs_eval_csv_{}_task".format(model.replace(".","_")),
    source_project_dataset_table="{}.{}_eval_data".format(DESTINATION_DATASET, model.replace(".","_")),
    destination_cloud_storage_uris=[eval_files + "{}/eval-*.csv".format(model.replace(".","_"))],
    export_format="CSV",
    print_header=False,
    dag=dag
  )


  # ML Engine training job
  job_id = "taxifare_{}_{}".format(model.replace(".","_"), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
  output_dir = BUCKET + "/taxifare/trained_model/{}".format(model.replace(".","_"))
  job_dir = JOB_DIR + "/" + job_id
  training_args = [
    "--job-dir", job_dir,
    "--train_data_paths", train_files,
    "--eval_data_paths", eval_files,
    "--output_dir", output_dir,
    "--train_steps", str(500),
    "--train_batch_size", str(32),
    "--eval_steps", str(500),
    "--eval_batch_size", str(32),
    "--nbuckets", str(8),
    "--hidden_units", "128,32,4"
  ]

  # Reference: https://airflow.apache.org/integration.html#cloud-ml-engine
  ml_engine_training_op = MLEngineTrainingOperator(
    task_id="ml_engine_training_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID,
    job_id=job_id,
    package_uris=[PACKAGE_URI],
    training_python_module="trainer.task",
    training_args=training_args,
    region=REGION,
    scale_tier="BASIC",
    runtime_version="1.13", 
    python_version="3.5",
    dag=dag
  )

  MODEL_NAME = "taxifare_"
  MODEL_VERSION = "v1"
  MODEL_LOCATION = BUCKET + "/taxifare/saved_model/"

  bash_remove_old_saved_model_op = BashOperator(
    task_id="bash_remove_old_saved_model_{}_task".format(model.replace(".","_")),
    bash_command="if gsutil ls {0} 2> /dev/null; then gsutil -m rm -rf {0}/*; else true; fi".format(MODEL_LOCATION + model.replace(".","_")),
    dag=dag
  )

  bash_copy_new_saved_model_op = BashOperator(
    task_id="bash_copy_new_saved_model_{}_task".format(model.replace(".","_")),
    bash_command="gsutil -m rsync -d -r `gsutil ls {0}/export/exporter/ | tail -1` {1}".format(output_dir, MODEL_LOCATION + model.replace(".","_")),
    dag=dag
  )

  # Create model on ML-Engine
  bash_ml_engine_models_list_op = BashOperator(
    task_id="bash_ml_engine_models_list_{}_task".format(model.replace(".","_")),
    xcom_push=True,
    bash_command="gcloud ml-engine models list --filter='name:{0}'".format(MODEL_NAME + model.replace(".","_")),
    dag=dag
  )

  def check_if_model_already_exists(templates_dict, **kwargs):
    cur_model = templates_dict["model"].replace(".","_")
    ml_engine_models_list = kwargs["ti"].xcom_pull(task_ids="bash_ml_engine_models_list_{}_task".format(cur_model))
    logging.info("check_if_model_already_exists: {}: ml_engine_models_list = \n{}".format(cur_model, ml_engine_models_list))
    create_model_task = "ml_engine_create_model_{}_task".format(cur_model)
    dont_create_model_task = "dont_create_model_dummy_branch_{}_task".format(cur_model)
    if len(ml_engine_models_list) == 0 or ml_engine_models_list == "Listed 0 items.":
      return create_model_task
    return dont_create_model_task

  check_if_model_already_exists_op = BranchPythonOperator(
    task_id="check_if_model_already_exists_{}_task".format(model.replace(".","_")),
    templates_dict={"model": model.replace(".","_")},
    python_callable=check_if_model_already_exists,
    provide_context=True,
    dag=dag
  )

  ml_engine_create_model_op = MLEngineModelOperator(
    task_id="ml_engine_create_model_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model={"name": MODEL_NAME + model.replace(".","_")}, 
    operation="create",
    dag=dag
  )

  create_model_dummy_op = DummyOperator(
    task_id="create_model_dummy_{}_task".format(model.replace(".","_")),
    trigger_rule="all_done",
    dag=dag
  )

  dont_create_model_dummy_branch_op = DummyOperator(
    task_id="dont_create_model_dummy_branch_{}_task".format(model.replace(".","_")),
    dag=dag
  )

  dont_create_model_dummy_op = DummyOperator(
    task_id="dont_create_model_dummy_{}_task".format(model.replace(".","_")),
    trigger_rule="all_done",
    dag=dag
  )

  # Create version of model on ML-Engine
  bash_ml_engine_versions_list_op = BashOperator(
    task_id="bash_ml_engine_versions_list_{}_task".format(model.replace(".","_")),
    xcom_push=True,
    bash_command="gcloud ml-engine versions list --model {0} --filter='name:{1}'".format(MODEL_NAME + model.replace(".","_"), MODEL_VERSION),
    dag=dag
  )

  def check_if_model_version_already_exists(templates_dict, **kwargs):
    cur_model = templates_dict["model"].replace(".","_")
    ml_engine_versions_list = kwargs["ti"].xcom_pull(task_ids="bash_ml_engine_versions_list_{}_task".format(cur_model))
    logging.info("check_if_model_version_already_exists: {}: ml_engine_versions_list = \n{}".format(cur_model, ml_engine_versions_list))
    create_version_task = "ml_engine_create_version_{}_task".format(cur_model)
    create_other_version_task = "ml_engine_create_other_version_{}_task".format(cur_model)
    if len(ml_engine_versions_list) == 0 or ml_engine_versions_list == "Listed 0 items.":
      return create_version_task
    return create_other_version_task

  check_if_model_version_already_exists_op = BranchPythonOperator(
    task_id="check_if_model_version_already_exists_{}_task".format(model.replace(".","_")), 
    templates_dict={"model": model.replace(".","_")},
    python_callable=check_if_model_version_already_exists,
    provide_context=True,
    dag=dag
  )

  OTHER_VERSION_NAME = "v_{0}".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")[0:12])

  ml_engine_create_version_op = MLEngineVersionOperator(
    task_id="ml_engine_create_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=MODEL_VERSION, 
    version={
      "name": MODEL_VERSION,
      "deploymentUri": MODEL_LOCATION + model.replace(".","_"),
      "runtimeVersion": "1.13",
      "framework": "TENSORFLOW",
      "pythonVersion": "3.5",
    },
    operation="create",
    dag=dag
  )

  ml_engine_create_other_version_op = MLEngineVersionOperator(
    task_id="ml_engine_create_other_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=OTHER_VERSION_NAME, 
    version={
      "name": OTHER_VERSION_NAME,
      "deploymentUri": MODEL_LOCATION + model.replace(".","_"),
      "runtimeVersion": "1.13",
      "framework": "TENSORFLOW",
      "pythonVersion": "3.5",
    },
    operation="create",
    dag=dag
  )

  ml_engine_set_default_version_op = MLEngineVersionOperator(
    task_id="ml_engine_set_default_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=MODEL_VERSION, 
    version={"name": MODEL_VERSION}, 
    operation="set_default",
    dag=dag
  )

  ml_engine_set_default_other_version_op = MLEngineVersionOperator(
    task_id="ml_engine_set_default_other_version_{}_task".format(model.replace(".","_")),
    project_id=PROJECT_ID, 
    model_name=MODEL_NAME + model.replace(".","_"), 
    version_name=OTHER_VERSION_NAME, 
    version={"name": OTHER_VERSION_NAME}, 
    operation="set_default",
    dag=dag
  )

  # Build dependency graph, set_upstream dependencies for all tasks
  bq_check_train_data_op.set_upstream(bq_train_data_op)
  bq_check_eval_data_op.set_upstream(bq_eval_data_op)

  bash_remove_old_data_op.set_upstream([bq_check_train_data_op, bq_check_eval_data_op])

  bq_export_gcs_train_csv_op.set_upstream([bash_remove_old_data_op])
  bq_export_gcs_eval_csv_op.set_upstream([bash_remove_old_data_op])

  ml_engine_training_op.set_upstream([bq_export_gcs_train_csv_op, bq_export_gcs_eval_csv_op])

  bash_remove_old_saved_model_op.set_upstream(ml_engine_training_op)
  bash_copy_new_saved_model_op.set_upstream(bash_remove_old_saved_model_op)

  bash_ml_engine_models_list_op.set_upstream(ml_engine_training_op)
  check_if_model_already_exists_op.set_upstream(bash_ml_engine_models_list_op)

  ml_engine_create_model_op.set_upstream(check_if_model_already_exists_op)
  create_model_dummy_op.set_upstream(ml_engine_create_model_op)
  dont_create_model_dummy_branch_op.set_upstream(check_if_model_already_exists_op)
  dont_create_model_dummy_op.set_upstream(dont_create_model_dummy_branch_op)

  bash_ml_engine_versions_list_op.set_upstream([dont_create_model_dummy_op, create_model_dummy_op])
  check_if_model_version_already_exists_op.set_upstream(bash_ml_engine_versions_list_op)

  ml_engine_create_version_op.set_upstream([bash_copy_new_saved_model_op, check_if_model_version_already_exists_op])
  ml_engine_create_other_version_op.set_upstream([bash_copy_new_saved_model_op, check_if_model_version_already_exists_op])

  ml_engine_set_default_version_op.set_upstream(ml_engine_create_version_op)
  ml_engine_set_default_other_version_op.set_upstream(ml_engine_create_other_version_op)
