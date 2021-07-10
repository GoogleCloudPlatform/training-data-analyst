
# Code adapted for use in this demo from 
# https://medium.com/@gruby/extracting-data-from-bigquery-table-to-parquet-into-gcs-using-cloud-dataflow-and-apache-beam-c63ce819b06a

"""Beam code for extracting data from BQ to parquet using the
   pyarrow package."""

# Usage:
#  $ python bq_to_parquet.py --bql BQ_QUERY --output GCS_LOCATION
# *
# * bql: BigQuery Standard SQL statement to extract required columns and rows
# * output: GCS output location for parquet files

from __future__ import absolute_import

import argparse
import logging

import apache_beam as beam
import pyarrow
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import bigquery


def get_parquet_schema(project, dataset, table):
    '''Return parquet schema for specified table.'''
    project_id = project
    dataset_id = dataset
    table_id = table
    data_type_mapping = {
        'STRING': pyarrow.string(),
        'BYTES': pyarrow.string(),
        'INTEGER': pyarrow.int64(),
        'FLOAT': pyarrow.float64(),
        'BOOLEAN': pyarrow.bool_(),
        'TIMESTAMP': pyarrow.timestamp(unit='s'),
        'DATE': pyarrow.date64(),
        'DATETIME': pyarrow.timestamp(unit='s'),
        ## Uncomment lines ONLY if you have nested and repeated fields present.
        # 'ARRAY': pyarrow.list_(),
        # 'RECORD': pyarrow.dictionary()
    }
    client = bigquery.Client(project=project_id)
    dataset_ref = client.dataset(dataset_id, project=project)
    table_ref = dataset_ref.table(table_id)
    table = client.get_table(table_ref)
    parquet_schema = pyarrow.schema([])
    for column in table.schema:
        parquet_schema = parquet_schema.append(
            pyarrow.field(column.name, data_type_mapping[column.field_type]))
    return parquet_schema


def run(argv=None):
    '''Main entry point: defines and runs the BQ extraction pipeline'''
    parser = argparse.ArgumentParser()
    # Custom arguments for BigQuery SQL and GCS output location
    parser.add_argument('--bql',
                        dest='bql',
                        help='BigQuery Standard SQL statement to define data to be extracted.')
    parser.add_argument('--output',
                        dest='output',
                        help='GCS output location for parquet files.')
    known_args, pipeline_args = parser.parse_known_args(argv)
    bq_table_source = known_args.bql.split('`')[1].split('.')
    parquet_schema = get_parquet_schema(bq_table_source[0], bq_table_source[1], bq_table_source[2])
    options = PipelineOptions(pipeline_args)

    # Instantiate a pipeline with all the pipeline options
    p = beam.Pipeline(options=options)
    # Processing and structure of pipeline
    p \
    | 'Input: Query BQ Table' >> beam.io.Read(beam.io.BigQuerySource(
        query=known_args.bql,
        use_standard_sql=True)) \
    | 'Output: Export to Parquet' >> beam.io.parquetio.WriteToParquet(
        file_path_prefix=known_args.output,
        schema=parquet_schema,
        file_name_suffix='.parquet',
        num_shards=1 # Remove this line for larger datasets and concatenate downstream.
    )

    result = p.run()
    result.wait_until_finish()  # Makes job to display all the logs. Remove this line if you
                                # don't wish to see this information in the console.
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
