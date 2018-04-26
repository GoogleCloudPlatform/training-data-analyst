import apache_beam as beam
import logging
from apache_beam.transforms.window import FixedWindows


from model import inference
from datetime import  datetime
import json

PROJECT = 'ksalama-gcp-playground'
DATASET = 'playground_ds'
TABLE = 'babyweight_estimates'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
WINDOW_SIZE = 5

schema_definition = {
    'source_id':'INTEGER',
    'source_timestamp':'TIMESTAMP',
    'predict_timestamp':'TIMESTAMP',
    'estimated_weight':'FLOAT',
    'is_male': 'STRING',
    'mother_age': 'FLOAT',
    'mother_race': 'STRING',
    'plurality': 'FLOAT',
    'gestation_weeks': 'INTEGER',
    'mother_married': 'BOOLEAN',
    'cigarette_use': 'BOOLEAN',
    'alcohol_use': 'BOOLEAN'
}

schema = str(schema_definition).replace('{', '').replace('}', '').replace("'", '').replace(' ', '')


def estimate(messages, inference_type):

    if not isinstance(messages, list):
        messages = [messages]

    instances = list(
        map(lambda message: json.loads(message),
            messages)
    )

    source_ids = list(
        map(lambda instance: instance.pop('source_id'),
            instances)

    )

    source_timestamps = list(
        map(lambda instance: instance.pop('source_timestamp'),
            instances)
    )

    if inference_type == 'local':
        estimated_weights = inference.estimate_local(instances)
    elif inference_type == 'cmle':
        estimated_weights = inference.estimate_cmle(instances)
    else:
        estimated_weights = 'NA'

    for i in range(len(instances)):
        instance = instances[i]
        instance['estimated_weight'] = estimated_weights[i]
        instance['source_id'] = source_ids[i]
        instance['source_timestamp'] = source_timestamps[i]
        instance['predict_timestamp'] = datetime.now().strftime(TIME_FORMAT)

    logging.info(instances)

    return instances


def run_pipeline(inference_type, pubsub_topic, runner, args=None):

    options = beam.pipeline.PipelineOptions(flags=[], **args)

    pipeline = beam.Pipeline(runner, options=options)

    (
            pipeline
            | 'Read from PubSub' >> beam.io.ReadStringsFromPubSub(topic=pubsub_topic)
            | 'Estimate Targets - {}'.format(inference_type) >> beam.FlatMap(lambda message: estimate(message, inference_type))
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(project=PROJECT, dataset=DATASET, table=TABLE, schema=schema,
                                                             create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED)
    )

    pipeline.run()


def run_pipeline_with_micro_batches(inference_type, pubsub_topic, runner, args=None):

    options = beam.pipeline.PipelineOptions(flags=[], **args)

    pipeline = beam.Pipeline(runner, options=options)

    (
            pipeline
            | 'Read from PubSub' >> beam.io.ReadStringsFromPubSub(topic=pubsub_topic)
            | 'Windowing into Micro-batches' >> beam.WindowInto(FixedWindows(size=WINDOW_SIZE))
            | 'Estimate Targets - {}'.format(inference_type) >> beam.FlatMap(lambda messages: estimate(messages, inference_type))
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(project=PROJECT, dataset=DATASET, table=TABLE, schema=schema,
                                                             create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED)
    )



    pipeline.run()
