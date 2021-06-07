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
from apache_beam.transforms.combiners import CountCombineFn
from apache_beam.runners import DataflowRunner
from apache_beam.transforms.trigger import AfterProcessingTime, AfterWatermark

class TaxiRide(typing.NamedTuple):
    ride_id: str
    point_idx: int
    latitude: float
    longitude: float
    timestamp: str
    meter_reading: float
    meter_increment: float
    ride_status: str
    passenger_count: int

beam.coders.registry.register_coder(TaxiRide, beam.coders.RowCoder)

def parse_json(element):
    row = json.loads(element.decode('utf-8'))
    return TaxiRide(**row)

class GetTimestampFn(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        window_start = window.start.to_utc_datetime().strftime("%Y-%m-%dT%H:%M:%S")
        output = {'page_views': element, 'timestamp': window_start}
        yield output

def run():
    # Command line arguments
    parser = argparse.ArgumentParser(description='Load from PubSub into BigQuery')
    parser.add_argument('--project',required=True, help='Specify Google Cloud project')
    parser.add_argument('--region', required=True, help='Specify Google Cloud region')
    parser.add_argument('--staging_location', required=True, help='Specify Cloud Storage bucket for staging')
    parser.add_argument('--temp_location', required=True, help='Specify Cloud Storage bucket for temp')
    parser.add_argument('--accum_mode', required=True, help='Accumulation mode for pipeline')
    

    opts, pipeline_args = parser.parse_known_args()

    options = PipelineOptions(pipeline_args, save_main_session=True)

    options.view_as(GoogleCloudOptions).job_name = f"{opts.accum_mode}-{time.time_ns()}"
    options.view_as(GoogleCloudOptions).project = opts.project
    options.view_as(GoogleCloudOptions).region = opts.region
    options.view_as(GoogleCloudOptions).staging_location = opts.staging_location
    options.view_as(GoogleCloudOptions).temp_location = opts.temp_location
    options.view_as(StandardOptions).runner = 'DataflowRunner'

    table_schema = {
        "fields": [
            {
                "name": "taxi_events",
                "type": "INTEGER"
            },
            {
                "name": "timestamp",
                "type": "STRING"
            },

        ]
    }

    input_topic = "projects/pubsub-public-data/topics/taxirides-realtime"
    output_table = f"{opts.project}:dataflow_demos.{opts.accum_mode}"

    if opts.accum_mode == 'accumulating':
        accum_mode = beam.transforms.trigger.AccumulationMode.ACCUMULATING
    elif opts.accum_mode == 'discarding':
        accum_mode = beam.transforms.trigger.AccumulationMode.DISCARDING
    else:
        raise ValueError('Invalid accumulation mode value. Use \'accumulating\' or \'discarding\' ')

    p = beam.Pipeline(options=options)

    (p | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(input_topic)
       | 'ParseJson' >> beam.Map(parse_json).with_output_types(TaxiRide)
       | 'WindowByMinute' >> beam.WindowInto(beam.window.FixedWindows(60),
                                              trigger=AfterWatermark(early=AfterProcessingTime(10)),
                                              accumulation_mode=accum_mode)
       | "CountPerMinute" >> beam.CombineGlobally(CountCombineFn()).without_defaults()
       | "AddWindowTimestamp" >> beam.ParDo(GetTimestampFn())
       | 'WriteAggToBQ' >> beam.io.WriteToBigQuery(
            output_table,
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            )
    )

    logging.getLogger().setLevel(logging.INFO)
    logging.info("Building pipeline ...")

    p.run()

if __name__ == '__main__':
  run()
