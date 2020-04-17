import argparse
import os

from google.cloud import bigquery
from google.cloud.bigquery.job import ExtractJobConfig


DATASET = "taxifare"
TRAIN_TABLE = "feateng_training_data"
VALID_TABLE = "feateng_valid_data"

TRAIN_SQL = """ CREATE OR REPLACE TABLE taxifare.feateng_training_data AS

SELECT
    (tolls_amount + fare_amount) AS fare_amount,
    pickup_datetime,
    pickup_longitude AS pickuplon,
    pickup_latitude AS pickuplat,
    dropoff_longitude AS dropofflon,
    dropoff_latitude AS dropofflat,
    passenger_count*1.0 AS passengers,
    'unused' AS key
FROM `nyc-tlc.yellow.trips`
WHERE ABS(MOD(FARM_FINGERPRINT(CAST(pickup_datetime AS STRING)), 1000)) = 1
AND
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
"""

VALID_SQL = """
CREATE OR REPLACE TABLE taxifare.feateng_valid_data AS

SELECT
    (tolls_amount + fare_amount) AS fare_amount,
    pickup_datetime,
    pickup_longitude AS pickuplon,
    pickup_latitude AS pickuplat,
    dropoff_longitude AS dropofflon,
    dropoff_latitude AS dropofflat,
    passenger_count*1.0 AS passengers,
    'unused' AS key
FROM `nyc-tlc.yellow.trips`
WHERE ABS(MOD(FARM_FINGERPRINT(CAST(pickup_datetime AS STRING)), 10000)) = 2
AND
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
"""


def export_table_to_gcs(dataset_ref, source_table, destination_uri):
    table_ref = dataset_ref.table(source_table)

    config = ExtractJobConfig()
    config.print_header = False

    extract_job = bq.extract_table(
        table_ref,
        destination_uri,
        location="US",
        job_config=config,
    )
    extract_job.result()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bucket",
        help = "GCS bucket where datasets will be exported.",
        required = True
    )
    args = parser.parse_args()

    gs = "gs://"
    bucket = args.bucket if gs in args.bucket else os.path.join(gs, args.bucket)
    datadir = os.path.join(bucket, DATASET, 'data')
    train_export_path = os.path.join(datadir, "taxi-train-*.csv")
    valid_export_path = os.path.join(datadir, "taxi-valid-*.csv")

    bq = bigquery.Client()

    dataset_ref = bigquery.Dataset(bq.dataset("taxifare"))

    try:
        bq.create_dataset(dataset_ref)
        print("Dataset created")
    except:
        print("Dataset already exists")

    print("Creating the training dataset...")
    bq.query(TRAIN_SQL).result()

    print("Creating the validation dataset...")
    bq.query(VALID_SQL).result()

    print("Exporting training dataset to GCS", train_export_path)
    export_table_to_gcs(dataset_ref, TRAIN_TABLE, train_export_path)

    print("Exporting validation dataset to GCS", valid_export_path)
    export_table_to_gcs(dataset_ref, VALID_TABLE, valid_export_path)

