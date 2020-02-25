import apache_beam as beam
import logging
from apache_beam.transforms.window import FixedWindows

from model import inference
from datetime import datetime
import json

from google.cloud import pubsub
from google.cloud import bigquery


BQ_SCHEMA_DEF = {
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


def prepare_steaming_source(project_id, pubsub_topic, pubsub_subscription):

    # create pubsub topic

    pubsub_client = pubsub.Client(project=project_id)
    topic = pubsub_client.topic(pubsub_topic)

    if topic.exists():
        print('Deleting pub/sub topic {}...'.format(pubsub_topic))
        topic.delete()

    print('Creating pub/sub topic {}...'.format(pubsub_topic))
    topic.create()
    print('Pub/sub topic {} is up and running'.format(pubsub_topic))

    subscription = topic.subscription(pubsub_subscription)
    if subscription.exists():
        print('Deleting pub/sub subscription {}...'.format(pubsub_subscription))
        subscription.delete()

    print('Creating pub/sub subscription {}...'.format(pubsub_subscription))
    subscription.create()
    print('Pub/sub topic {} is up and running'.format(pubsub_subscription))

    print("")


def prepare_steaming_sink(project_id, bq_dataset, bq_table):

    # create BigQuery table
    schema = [bigquery.SchemaField(field_name, data_type)
              for field_name, data_type in BQ_SCHEMA_DEF.items()]

    bq_client = bigquery.Client(project=project_id)
    dataset = bigquery.Dataset(bq_dataset, bq_client)
    table = bigquery.Table(bq_table, dataset, schema=schema)

    if table.exists():
        print('Deleting BQ Table {}...'.format(bq_table))
        table.delete()

    print('Creating BQ Table {}...'.format(bq_table))
    table.create()

    print('BQ Table {} is up and running'.format(bq_table))
    print("")


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
        instance['predict_timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    logging.info(instances)

    return instances


def run_pipeline(inference_type, project, pubsub_topic, pubsub_subscription, bq_dataset, bq_table, runner, args=None):

    prepare_steaming_source(project, pubsub_topic, pubsub_subscription)

    prepare_steaming_sink(project, bq_dataset, bq_table)

    pubsub_subscription_url = "projects/{}/subscriptions/{}".format(project, pubsub_subscription)

    options = beam.pipeline.PipelineOptions(flags=[], **args)

    pipeline = beam.Pipeline(runner, options=options)

    (

            pipeline
            | 'Read from PubSub' >> beam.io.ReadStringsFromPubSub(subscription=pubsub_subscription_url, id_label="source_id")
            | 'Estimate Targets - {}'.format(inference_type) >> beam.FlatMap(lambda message: estimate(message, inference_type))
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(project=project,
                                                             dataset=bq_dataset,
                                                             table=bq_table)
    )

    pipeline.run()


#[START micro-batching]
def run_pipeline_with_micro_batches(inference_type, project,
                                    pubsub_topic, pubsub_subscription,
                                    bq_dataset, bq_table,
                                    window_size, runner, args=None):

    prepare_steaming_source(project, pubsub_topic, pubsub_subscription)
    prepare_steaming_sink(project, bq_dataset, bq_table)
    pubsub_subscription_url = "projects/{}/subscriptions/{}".format(project, pubsub_subscription)
    options = beam.pipeline.PipelineOptions(flags=[], **args)

    pipeline = beam.Pipeline(runner, options=options)
    (
            pipeline
            | 'Read from PubSub' >> beam.io.ReadStringsFromPubSub(subscription=pubsub_subscription_url, id_label="source_id")
            | 'Micro-batch - Window Size: {} Seconds'.format(window_size) >> beam.WindowInto(FixedWindows(size=window_size))
            | 'Estimate Targets - {}'.format(inference_type) >> beam.FlatMap(lambda messages: estimate(messages, inference_type))
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(project=project,
                                                             dataset=bq_dataset,
                                                             table=bq_table
                                                             )
    )

    pipeline.run()
#[END micro-batching]

