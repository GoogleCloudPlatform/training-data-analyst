import argparse
import time
import logging
import json
import typing
import apache_beam as beam
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.transforms.combiners import CountCombineFn
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

class PerUserAggregation(typing.NamedTuple):
    user_id: str
    page_views: int
    total_bytes: int
    max_bytes: int
    min_bytes: int

beam.coders.registry.register_coder(CommonLog, beam.coders.RowCoder)
beam.coders.registry.register_coder(PerUserAggregation, beam.coders.RowCoder)

def parse_json(element):
    row = json.loads(element)
    return CommonLog(**row)

def to_dict(element):
    return element._asdict()


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
    parser.add_argument('--table_name', required=True, help='BigQuery table name')

    opts = parser.parse_args()

    # Setting up the Beam pipeline options
    options = PipelineOptions(save_main_session=True)
    options.view_as(GoogleCloudOptions).project = opts.project
    options.view_as(GoogleCloudOptions).region = opts.region
    options.view_as(GoogleCloudOptions).staging_location = opts.staging_location
    options.view_as(GoogleCloudOptions).temp_location = opts.temp_location
    options.view_as(GoogleCloudOptions).job_name = '{0}{1}'.format('batch-user-traffic-pipeline-',time.time_ns())
    options.view_as(StandardOptions).runner = opts.runner

    input_path = opts.input_path
    table_name = opts.table_name

    # Table schema for BigQuery
    table_schema = {
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

    # Create the pipeline
    p = beam.Pipeline(options=options)



    (p | 'ReadFromGCS' >> beam.io.ReadFromText(input_path)
       | 'ParseJson' >> beam.Map(parse_json).with_output_types(CommonLog)
       | 'PerUserAggregations' >> beam.GroupBy('user_id')
                                      .aggregate_field('user_id', CountCombineFn(), 'page_views')
                                      .aggregate_field('num_bytes', sum, 'total_bytes')
                                      .aggregate_field('num_bytes', max, 'max_bytes')
                                      .aggregate_field('num_bytes', min, 'min_bytes')
                                      .with_output_types(PerUserAggregation)
       | 'ToDict' >> beam.Map(to_dict)
       | 'WriteToBQ' >> beam.io.WriteToBigQuery(
            table_name,
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE
            )
    )

    logging.getLogger().setLevel(logging.INFO)
    logging.info("Building pipeline ...")

    p.run()

if __name__ == '__main__':
  run()
