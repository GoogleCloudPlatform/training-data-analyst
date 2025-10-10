import argparse
import time
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.transforms.combiners import CountCombineFn

# Import our custom classes and functions from the utility file.
# This makes them available to the main script.
from pipeline_utils import CommonLog, parse_json, add_timestamp, GetTimestampFn

# ### main function
def run():
    # Command line arguments
    parser = argparse.ArgumentParser(description='Load from Json into BigQuery')
    parser.add_argument('--project', required=True, help='Specify Google Cloud project')
    parser.add_argument('--region', required=True, help='Specify Google Cloud region')
    parser.add_argument('--staging_location', required=True, help='Specify Cloud Storage bucket for staging')
    parser.add_argument('--temp_location', required=True, help='Specify Cloud Storage bucket for temp')
    parser.add_argument('--runner', required=True, help='Specify Apache Beam Runner')
    parser.add_argument('--input_path', required=True, help='Path to events.json')
    parser.add_argument('--table_name', required=True, help='BigQuery table name')
    # The --setup_file argument is now expected from the command line.
    parser.add_argument('--setup_file', required=True, help='Path to setup.py file')

    opts = parser.parse_args()

    # Setting up the Beam pipeline options.
    # Update PipelineOptions to include pickle_library='dill' and save_main_session=True
    options = PipelineOptions(
        pickle_library='dill',
        save_main_session=True
    )

    google_cloud_options = options.view_as(GoogleCloudOptions)
    google_cloud_options.project = opts.project
    google_cloud_options.region = opts.region
    google_cloud_options.staging_location = opts.staging_location
    google_cloud_options.temp_location = opts.temp_location
    google_cloud_options.job_name = '{0}{1}'.format('batch-minute-traffic-pipeline-', time.time_ns())
    options.view_as(StandardOptions).runner = opts.runner

    input_path = opts.input_path
    table_name = opts.table_name

    # Table schema for BigQuery
    table_schema = {
        "fields": [
            { "name": "page_views", "type": "INTEGER" },
            { "name": "timestamp", "type": "STRING" },
        ]
    }

    # Create the pipeline
    p = beam.Pipeline(options=options)

    (p | 'ReadFromGCS' >> beam.io.ReadFromText(input_path)
       | 'ParseJson' >> beam.Map(parse_json).with_output_types(CommonLog)

       # =================================================================
       # Task 5: Add timestamps to each element
       # The `add_timestamp` function (defined in pipeline_utils.py) parses the
       # timestamp string from each log record and attaches it to the element
       # as a proper Beam timestamp, which is required for windowing.
       # =================================================================
       | 'AddEventTimestamp' >> beam.Map(add_timestamp)

       # =================================================================
       # Task 6: Window into one-minute windows
       # This transform groups elements into fixed-size, non-overlapping windows
       # of 60 seconds (one minute) based on their event timestamps.
       # =================================================================
       | "WindowByMinute" >> beam.WindowInto(beam.window.FixedWindows(60))

       # =================================================================
       # Task 7: Count events per window
       # This combiner counts the number of elements within each one-minute window.
       # `.without_defaults()` ensures that no output is generated for empty windows.
       # =================================================================
       | "CountPerMinute" >> beam.CombineGlobally(CountCombineFn()).without_defaults()

       # =================================================================
       # Task 8: Convert back to a row and add timestamp
       # The `GetTimestampFn` (defined in pipeline_utils.py) takes the integer count
       # for each window and formats it into a dictionary, adding the window's
       # start time as a string to match the BigQuery schema.
       # =================================================================
       | "AddWindowTimestamp" >> beam.ParDo(GetTimestampFn())

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
