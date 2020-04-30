"""A streaming dataflow pipeline to count pub/sub messages.
"""

from __future__ import absolute_import

import argparse
import logging
from datetime import datetime

from past.builtins import unicode

import apache_beam as beam
import apache_beam.transforms.window as window
from apache_beam.examples.wordcount import WordExtractingDoFn
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.io import WriteToText


class CountFn(beam.CombineFn):
    def create_accumulator(self):
        return 0

    def add_input(self, count, input):
        return count + 1

    def merge_accumulators(self, accumulators):
        return sum(accumulators)

    def extract_output(self, count):
        return count


def run(argv=None):
    """Build and run the pipeline."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
            '--project',
            help=('Google Cloud Project ID'),
            required=True)
    parser.add_argument(
            '--input_topic',
            help=('Google Cloud PubSub topic name '),
            required=True)

    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(
        pipeline_args.append('--project={}'.format(known_args.project)))
    pipeline_options.view_as(SetupOptions).save_main_session = True
    pipeline_options.view_as(StandardOptions).streaming = True

    p = beam.Pipeline(options=pipeline_options)

    TOPIC = 'projects/{}/topics/{}'.format(known_args.project,
                                           known_args.input_topic)
    # this table needs to exist
    table_spec = '{}:taxifare.traffic_realtime'.format(known_args.project)

    def to_bq_format(count):
        """BigQuery writer requires rows to be stored as python dictionary"""
        return {'trips_last_5min': count,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    pipeline = (p
                | 'read_from_pubsub' >> beam.io.ReadFromPubSub(topic=TOPIC).with_output_types(bytes)
                | 'window' >> beam.WindowInto(window.SlidingWindows(
                    size=300,
                    period=15))
                | 'count' >> beam.CombineGlobally(CountFn()).without_defaults()
                | 'format_for_bq' >> beam.Map(to_bq_format)
                | 'write_to_bq' >> beam.io.WriteToBigQuery(
                    table_spec,
                    # WRITE_TRUNCATE not supported for streaming
                    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                    create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER)
                )

    result = p.run()
    # result.wait_until_finish() #only do this if running with DirectRunner

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
