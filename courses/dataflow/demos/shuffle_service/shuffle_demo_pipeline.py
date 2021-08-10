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
from apache_beam.runners import DataflowRunner

def extract_platform(element):
    platform = element.pop('dependency_platform')
    #Artifical fanout of data
    for k in range(1):
        yield (platform, 1)

def count_per_key(element):
    key = element[0]
    count = sum(element[1])
    return (key, count)

def to_dict(element):
    result = {}
    result['platform'] = element[0]
    result['dep_count'] = element[1]
    return result

class CountPerPlatform(beam.PTransform):
    def expand(self, pcoll):
        output = (pcoll | 'GBK' >> beam.GroupByKey()
                        | 'CountPerKey' >> beam.Map(count_per_key)
                        )
        return output

def run():
    # Command line arguments
    parser = argparse.ArgumentParser(description='Load from Json into BigQuery')
    parser.add_argument('--project',required=True, help='Specify Google Cloud project')
    parser.add_argument('--region', required=True, help='Specify Google Cloud region')
    parser.add_argument('--staging_location', required=True, help='Specify Cloud Storage bucket for staging')
    parser.add_argument('--temp_location', required=True, help='Specify Cloud Storage bucket for temp')
    

    opts, pipeline_args = parser.parse_known_args()

    options = PipelineOptions(pipeline_args, save_main_session=True)

    if pipeline_args:
        options.view_as(GoogleCloudOptions).job_name = '{0}{1}'.format('no-shuffle-pipeline-',time.time_ns())
    else: 
        options.view_as(GoogleCloudOptions).job_name = '{0}{1}'.format('shuffle-pipeline-',time.time_ns())
    
    
    options.view_as(GoogleCloudOptions).project = opts.project
    options.view_as(GoogleCloudOptions).region = opts.region
    options.view_as(GoogleCloudOptions).staging_location = opts.staging_location
    options.view_as(GoogleCloudOptions).temp_location = opts.temp_location
    options.view_as(StandardOptions).runner = 'DataflowRunner'

    table_schema = {
        "fields": [

            {
                "name": "platform",
                "type": "STRING"
            },
            {
                "name": "dep_count",
                "type": "INTEGER"
            }
        ]
    }

    input_table = 'bigquery-public-data:libraries_io.dependencies'
    output_table = f"{opts.project}:dataflow_demos.shuffle_demo"

    p = beam.Pipeline(options=options)

    (p | 'ReadFromBQ' >> beam.io.ReadFromBigQuery(table=input_table)
       | 'ExtractPlatform' >> beam.FlatMap(extract_platform)
       | 'CountPerPlatform' >> CountPerPlatform()
       | 'ToDict' >> beam.Map(to_dict)
       | 'WriteToBQ' >> beam.io.WriteToBigQuery(
            output_table,
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
