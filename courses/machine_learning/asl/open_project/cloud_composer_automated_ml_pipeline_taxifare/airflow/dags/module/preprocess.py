from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.operators.bigquery_check_operator import BigQueryCheckOperator
from airflow.contrib.operators.bigquery_to_gcs import BigQueryToCloudStorageOperator
from airflow.operators.bash_operator import BashOperator


def preprocess_tasks(model, dag, PROJECT_ID, BUCKET, DATA_DIR):
  # Constants
  # Specify your source BigQuery project, dataset, and table names
  SOURCE_BQ_PROJECT = "nyc-tlc"
  SOURCE_DATASET_TABLE_NAMES = "yellow.trips,green.trips_2014,green.trips_2015".split(",")

  # Specify your destination BigQuery dataset
  DESTINATION_DATASET = "taxifare"
  
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
  bq_export_gcs_train_csv_op = BigQueryToCloudStorageOperator(
    task_id="bq_export_gcs_train_csv_{}_task".format(model.replace(".","_")),
    source_project_dataset_table="{}.{}_train_data".format(DESTINATION_DATASET, model.replace(".","_")),
    destination_cloud_storage_uris=[DATA_DIR + "{}/train-*.csv".format(model.replace(".","_"))],
    export_format="CSV",
    print_header=False,
    dag=dag
  )

  bq_export_gcs_eval_csv_op = BigQueryToCloudStorageOperator(
    task_id="bq_export_gcs_eval_csv_{}_task".format(model.replace(".","_")),
    source_project_dataset_table="{}.{}_eval_data".format(DESTINATION_DATASET, model.replace(".","_")),
    destination_cloud_storage_uris=[DATA_DIR + "{}/eval-*.csv".format(model.replace(".","_"))],
    export_format="CSV",
    print_header=False,
    dag=dag
  )
  
  # Build dependency graph, set_upstream dependencies for all tasks
  bq_check_train_data_op.set_upstream(bq_train_data_op)
  bq_check_eval_data_op.set_upstream(bq_eval_data_op)

  bash_remove_old_data_op.set_upstream([bq_check_train_data_op, bq_check_eval_data_op])

  bq_export_gcs_train_csv_op.set_upstream(bash_remove_old_data_op)
  bq_export_gcs_eval_csv_op.set_upstream(bash_remove_old_data_op)
  
  return (bq_export_gcs_train_csv_op,
          bq_export_gcs_eval_csv_op)
