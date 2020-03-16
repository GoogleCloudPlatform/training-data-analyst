#!/bin/bash

# Code adapted for use in this demo from
# https://medium.com/@gruby/extracting-data-from-bigquery-table-to-parquet-into-gcs-using-cloud-dataflow-and-apache-beam-c63ce819b06a

# bash script to kick off job to export flights data from a public BigQuery
# dataset to parquet files in a GCS bucket. We are using the pyarrow package to
# do the conversion and you can change the query below to export a different
# table. This script is written with running on Cloud Shell in mind.

# Usage:
#  $ bash bq_to_parquet.sh project dataset table bucket region
# * project: GCP Project name for billing
# * dataset: BigQuery dataset where table is located
# * table: BigQuery table you wish to extract in parquet format
# * bucket: GCS storage bucket for staging, temp. storage, and final output
# * region: GCP region for Dataflow resources


# Note: The script is assuming you want to export an entire table or view.
# If you want to save the results for a more complex query, either save the results
# as a view, or you will need to adjust the get_parquet_schema function in the python script.


PROJECT=$1
DATASET=$2
TABLE=$3
BUCKET=$4
REGION=$5

sudo pip3 -q install -U apache-beam[gcp] pyarrow google-cloud-bigquery

python3 bq_to_parquet.py --bql "SELECT * FROM \`$PROJECT.$DATASET.$TABLE\`" \
                 --output gs://$BUCKET/beam_output/bq_to_parquet \
                 --project $PROJECT \
                 --job_name 'bigquerytoparquet' \
                 --staging_location gs://$BUCKET/staging \
                 --temp_location gs://$BUCKET/temp \
                 --region $REGION \
                 --runner DataflowRunner \
