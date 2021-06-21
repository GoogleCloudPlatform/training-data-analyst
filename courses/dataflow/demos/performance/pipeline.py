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

    opts, pipeline_opts = parser.parse_known_args()

    # Setting up the Beam pipeline options
    options = PipelineOptions(pipeline_opts, save_main_session=True)
    options.view_as(GoogleCloudOptions).project = opts.project
    options.view_as(GoogleCloudOptions).region = opts.region
    options.view_as(GoogleCloudOptions).staging_location = opts.staging_location
    options.view_as(GoogleCloudOptions).temp_location = opts.temp_location
    options.view_as(GoogleCloudOptions).job_name = '{0}{1}'.format('performance-demo-'
                                                                   ,time.time_ns())
    options.view_as(StandardOptions).runner = 'DataflowRunner'


    agg_output_path = f"{opts.project}/agg_output/"
    raw_output_path = f"{opts.project}/raw_output/"
    

    query = """
        SELECT user_id,
        COUNT(*) AS page_views, SUM(num_bytes) as total_bytes,
        MAX(num_bytes) AS max_bytes, MIN(num_bytes) as min_bytes
        FROM PCOLLECTION
        GROUP BY user_id
        """

    # Create the pipeline
    p = beam.Pipeline(options=options)

    logs = (p | 'ReadFromGCS' >> beam.io.ReadFromText('./users.csv')
              | 'ParseJson' >> beam.Map(parse_json).with_output_types(CommonLog))

    (logs | 'RawToDict' >> beam.Map(lambda row : row._asdict())
          #| 'WriteRawToText' >> beam.io.WriteToText(raw_output_path)
          )

    (logs | 'PerUserAggregations' >> SqlTransform(query, dialect='zetasql')
          | 'AggToDict' >> beam.Map(lambda row : row._asdict())
          #| 'WriteAggToText' >> beam.io.WriteToText(agg_output_path)
           )
    

    logging.getLogger().setLevel(logging.INFO)
    logging.info("Building pipeline ...")

    p.run()

if __name__ == '__main__':
  run()
