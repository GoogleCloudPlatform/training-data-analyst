import argparse
import time
import logging
import json
import typing
from datetime import datetime
import apache_beam as beam
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.transforms.sql import SqlTransform
from apache_beam.runners import DataflowRunner, DirectRunner

# ### functions and classes

class CommonLog(typing.NamedTuple):
    ip: str
    user_id: str
    lat: float
    lng: float
    timestamp: str
    event_timestamp: str
    http_request: str
    http_response: int
    num_bytes: int
    user_agent: str

beam.coders.registry.register_coder(CommonLog, beam.coders.RowCoder)

def parse_json(element):
    row = json.loads(element.decode('utf-8'))
    return row

class GetEventTimestampFn(beam.DoFn):
    def process(self, row, timestamp=beam.DoFn.TimestampParam):
        event_ts = timestamp.to_utc_datetime().strftime("%Y-%m-%dT%H:%M:%S")
        row['event_timestamp'] = event_ts
        yield CommonLog(**row)

class ParseAndGetEventTimestamp(beam.PTransform):
    def expand(self, pcoll):
        return (
            pcoll
            | 'ParseJson' >> beam.Map(parse_json)
            | 'GetEventTimestamp' >> beam.ParDo(GetEventTimestampFn())
            )

def to_dict(row):
    return {'page_views' : row.page_views,
            'start_time' : row.start_time}

# ### main

def run():
    # Command line arguments
    parser = argparse.ArgumentParser(description='Load from Json from Pub/Sub into BigQuery')
    parser.add_argument('--project',required=True, help='Specify Google Cloud project')
    parser.add_argument('--region', required=True, help='Specify Google Cloud region')
    parser.add_argument('--staging_location', required=True, help='Specify Cloud Storage bucket for staging')
    parser.add_argument('--temp_location', required=True, help='Specify Cloud Storage bucket for temp')
    parser.add_argument('--runner', required=True, help='Specify Apache Beam Runner')
    parser.add_argument('--input_topic', required=True, help='Input Pub/Sub Topic')
    parser.add_argument('--table_name', required=True, help='BigQuery table name for aggregate results')


    opts, pipeline_opts = parser.parse_known_args()

    # Setting up the Beam pipeline options
    options = PipelineOptions(pipeline_opts, save_main_session=True, streaming=True)
    options.view_as(GoogleCloudOptions).project = opts.project
    options.view_as(GoogleCloudOptions).region = opts.region
    options.view_as(GoogleCloudOptions).staging_location = opts.staging_location
    options.view_as(GoogleCloudOptions).temp_location = opts.temp_location
    options.view_as(GoogleCloudOptions).job_name = '{0}{1}'.format('streaming-minute-traffic-sql-pipeline-',time.time_ns())
    options.view_as(StandardOptions).runner = opts.runner

    input_topic = opts.input_topic
    table_name = opts.table_name

    # Table schema for BigQuery
    table_schema = {
        "fields": [
            {
                "name": "page_views",
                "type": "INTEGER"
            },
            {
                "name": "start_time",
                "type": "STRING"
            },

        ]
    }

    query = '''
        SELECT
            COUNT(*) AS page_views,
            STRING(window_start) AS start_time
        FROM
            TUMBLE(
                (SELECT TIMESTAMP(event_timestamp) AS ts FROM PCOLLECTION),
                DESCRIPTOR(ts),
                'INTERVAL 1 MINUTE')
        GROUP BY window_start
    '''

    # Create the pipeline
    p = beam.Pipeline(options=options)

    (p | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(input_topic)
       | 'ParseAndGetEventTimestamp' >> ParseAndGetEventTimestamp().with_output_types(CommonLog)
       | "CountPerMinute" >> SqlTransform(query, dialect='zetasql')
       | "ConvertToDict" >> beam.Map(to_dict)
       | 'WriteAggToBQ' >> beam.io.WriteToBigQuery(
            table_name,
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            )
    )

    logging.getLogger().setLevel(logging.INFO)
    logging.info("Building pipeline ...")

    p.run().wait_until_finish()

if __name__ == '__main__':
  run()
