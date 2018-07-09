"""An example Composer workflow integrating GCS and BigQuery.

A .csv is read from a GCS bucket to a BigQuery table; a query is made, and the
result is written back to a different BigQuery table within a new dataset.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.operators.gcs_to_bq import GoogleCloudStorageToBigQueryOperator
from airflow.operators.bash_operator import BashOperator

YESTERDAY = datetime.combine(
    datetime.today() - timedelta(days=1), datetime.min.time())
BQ_DATASET_NAME = 'gcp_example_dataset'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': YESTERDAY,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Solution: pass a schedule_interval argument to DAG instantiation.
with DAG('gcp_example_solution', default_args=default_args,
         schedule_interval=timedelta(hours=1)) as dag:
  create_bq_dataset_if_not_exist = """
    bq ls {0}
    if [ $? -ne 0 ]; then
      bq mk {0}
    fi
  """.format(BQ_DATASET_NAME)

  # Create destination dataset.
  t1 = BashOperator(
      task_id='create_destination_dataset',
      bash_command=create_bq_dataset_if_not_exist,
      dag=dag)

  # Create a bigquery table from a .csv file located in a GCS bucket
  # (gs://example-datasets/game_data_condensed.csv).
  # Store it in our dataset.
  t2 = GoogleCloudStorageToBigQueryOperator(
      task_id='gcs_to_bq',
      bucket='example-datasets',
      source_objects=['game_data_condensed.csv'],
      destination_project_dataset_table='{0}.gcp_example_table'
      .format(BQ_DATASET_NAME),
      schema_fields=[
          {'name': 'name', 'type': 'string', 'mode': 'nullable'},
          {'name': 'team', 'type': 'string', 'mode': 'nullable'},
          {'name': 'total_score', 'type': 'integer', 'mode': 'nullable'},
          {'name': 'timestamp', 'type': 'integer', 'mode': 'nullable'},
          {'name': 'window_start', 'type': 'string', 'mode': 'nullable'},
      ],
      write_disposition='WRITE_TRUNCATE')

  # Run example query (http://shortn/_BdF1UTEYOb) and save result to the
  # destination table.
  t3 = BigQueryOperator(
      task_id='bq_example_query',
      bql="""
        SELECT
          name, team, total_score
        FROM
          [bq_example.foobar]
        WHERE total_score > 15
        LIMIT 100;
      """,
      destination_dataset_table='{0}.gcp_example_query_result'
      .format(BQ_DATASET_NAME),
      write_disposition='WRITE_TRUNCATE')

  t1 >> t2 >> t3
