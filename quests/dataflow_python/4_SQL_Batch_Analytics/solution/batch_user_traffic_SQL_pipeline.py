import argparse
import time
import logging
import json
import typing
import apache_beam as beam
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.transforms.sql import SqlTransform
from apache_beam.runners import DataflowRunner, DirectRunner

# ### functions and classes

class CommonLog (typing.NamedTuple):
    ip: str
    user_id: str
    lat: float
    lng: float
    timestamp: str
    http_request: str
    http_response: int
    num_bytes: int
    user_agent: str

beam.coders.registry.register_coder(CommonLog, beam.coders.RowCoder)

def parse_json(element):
    row = json.loads(element)
    return CommonLog(**row)

# ### main

def run():
    # Command line arguments
    parser = argparse.ArgumentParser(description='Load from Json into BigQuery')
    parser.add_argument('--project',required=True, help='Specify Google Cloud project')
    parser.add_argument('--region', required=True, help='Specify Google Cloud region')
    parser.add_argument('--staging_location', required=True, help='Specify Cloud Storage bucket for staging')
    parser.add_argument('--temp_location', required=True, help='Specify Cloud Storage bucket for temp')
    parser.add_argument('--runner', required=True, help='Specify Apache Beam Runner')
    parser.add_argument('--input_path', required=True, help='Path to events.json')
    parser.add_argument('--raw_table_name', required=True, help='BigQuery table for raw data')
    parser.add_argument('--agg_table_name', required=True, help='BigQuery table for aggregated data')

    opts, pipeline_opts = parser.parse_known_args()

    # Setting up the Beam pipeline options
    options = PipelineOptions(pipeline_opts, save_main_session=True)
    options.view_as(GoogleCloudOptions).project = opts.project
    options.view_as(GoogleCloudOptions).region = opts.region
    options.view_as(GoogleCloudOptions).staging_location = opts.staging_location
    options.view_as(GoogleCloudOptions).temp_location = opts.temp_location
    options.view_as(GoogleCloudOptions).job_name = '{0}{1}'.format('batch-user-traffic-pipeline-sql-'
                                                                   ,time.time_ns())
    options.view_as(StandardOptions).runner = opts.runner

    input_path = opts.input_path
    agg_table_name = opts.agg_table_name
    raw_table_name = opts.raw_table_name

    # Table schema for BigQuery
    raw_table_schema = {
            "fields": [
                {
                    "name": "ip",
                    "type": "STRING"
                },
                {
                    "name": "user_id",
                    "type": "STRING"
                },
                {
                    "name": "lat",
                    "type": "FLOAT"
                },
                {
                    "name": "lng",
                    "type": "FLOAT"
                },
                {
                    "name": "timestamp",
                    "type": "STRING"
                },
                {
                    "name": "http_request",
                    "type": "STRING"
                },
                {
                    "name": "http_response",
                    "type": "INTEGER"
                },
                {
                    "name": "num_bytes",
                    "type": "INTEGER"
                },
                {
                    "name": "user_agent",
                    "type": "STRING"
                }
            ]
        }


    # Table schema for BigQuery
    agg_table_schema = {
        "fields": [

            {
                "name": "user_id",
                "type": "STRING"
            },
            {
                "name": "page_views",
                "type": "INTEGER"
            },
            {
                "name": "total_bytes",
                "type": "INTEGER"
            },
            {
                "name": "max_bytes",
                "type": "INTEGER"
            },
            {
                "name": "min_bytes",
                "type": "INTEGER"
            },
        ]
    }

    query = """
        SELECT user_id,
        COUNT(*) AS page_views, SUM(num_bytes) as total_bytes,
        MAX(num_bytes) AS max_bytes, MIN(num_bytes) as min_bytes
        FROM PCOLLECTION
        GROUP BY user_id
        """

    # Create the pipeline
    p = beam.Pipeline(options=options)

    logs = (p | 'ReadFromGCS' >> beam.io.ReadFromText(input_path)
              | 'ParseJson' >> beam.Map(parse_json).with_output_types(CommonLog))

    (logs | 'RawToDict' >> beam.Map(lambda row : row._asdict())
          | 'WriteRawToBQ' >> beam.io.WriteToBigQuery(
           raw_table_name,
           schema=raw_table_schema,
           create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
           write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE
      ))

    (logs | 'PerUserAggregations' >> SqlTransform(query, dialect='zetasql')
          | 'AggToDict' >> beam.Map(lambda row : row._asdict())
          | 'WriteAggToBQ' >> beam.io.WriteToBigQuery(
            agg_table_name,
            schema=agg_table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE
            )
    )

    logging.getLogger().setLevel(logging.INFO)
    logging.info("Building pipeline ...")

    p.run()

if __name__ == '__main__':
  run()
