import argparse
import time
import logging
import json
import typing
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions 
from apache_beam.transforms.combiners import CountCombineFn

# ## functions and classes ##

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
    # TODO 1: Finish defining class for schema


beam.coders.registry.register_coder(CommonLog, beam.coders.RowCoder)
# TODO 2: Register coder for PerUserAggregation

def parse_json(element):
    row = json.loads(element)
    return CommonLog(**row)

def to_dict(element):
    return element._asdict()


# ### main

def run(argv=None):
    # Command line arguments
    parser = argparse.ArgumentParser(description='Load from Json into BigQuery')
    
    # We only define arguments that are custom to THIS script's logic.
    parser.add_argument('--input_path', required=True, help='Path to events.json')
    parser.add_argument('--table_name', required=True, help='BigQuery table name')

    # Separate your custom args from the standard Beam args.
    known_args, pipeline_args = parser.parse_known_args(argv)

    # This automatically reads --project, --region, --runner, --worker_zone, etc.
    pipeline_options = PipelineOptions(pipeline_args, save_main_session=True)
    
    # Set a job name (optional, but good practice)
    job_name = f'batch-user-traffic-pipeline-{int(time.time_ns())}'
    # This line now works because GoogleCloudOptions is imported
    pipeline_options.view_as(GoogleCloudOptions).job_name = job_name

    # Table schema for BigQuery
    table_schema = {
        "fields": [
            {"name": "user_id", "type": "STRING"},
            {"name": "page_views", "type": "INTEGER"},
            {"name": "total_bytes", "type": "INTEGER"},
            {"name": "max_bytes", "type": "INTEGER"},
            {"name": "min_bytes", "type": "INTEGER"},
        ]
    }

    # Create the pipeline with the corrected options
    with beam.Pipeline(options=pipeline_options) as p:
        (p | 'ReadFromGCS' >> beam.io.ReadFromText(known_args.input_path) 
         | 'ParseJson' >> beam.Map(parse_json).with_output_types(CommonLog)
         | 'PerUserAggregations' >> beam.GroupBy('user_id')
             .aggregate_field('user_id', CountCombineFn(), 'page_views')
             .aggregate_field('num_bytes', sum, 'total_bytes')
             .aggregate_field('num_bytes', max, 'max_bytes')
             .aggregate_field('num_bytes', min, 'min_bytes')
             .with_output_types(PerUserAggregation)
         | 'ToDict' >> beam.Map(to_dict)
         | 'WriteToBQ' >> beam.io.WriteToBigQuery(
             known_args.table_name, 
             schema=table_schema,
             create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
             write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE
           )
        )

    logging.getLogger().setLevel(logging.INFO)
    logging.info("Building pipeline ...")

if __name__ == '__main__':
    run()