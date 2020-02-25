import apache_beam as beam
from model import inference
import json


HEADER = ['weight_pounds', 'is_male', 'mother_age', 'mother_race', 'plurality',
          'gestation_weeks', 'mother_married',
          'cigarette_use', 'alcohol_use']

SOURCE_QUERY = """
            SELECT
              weight_pounds,
              is_male,
              mother_age,
              mother_race,
              plurality,
              gestation_weeks,
              mother_married,
              cigarette_use,
              alcohol_use
            FROM
              publicdata.samples.natality
            WHERE year > 2000
            AND weight_pounds > 0
            AND mother_age > 0
            AND plurality > 0
            AND gestation_weeks > 0
            AND month > 0
"""


def get_source_query(sample_size):
    query = """
        SELECT *
        FROM {}
        LIMIT {}
    """.format(SOURCE_QUERY,sample_size)
    return query


def get_sample_size_desc(sample_size):
    desc = '({}{} Rows)'
    if sample_size >= 1000000:
        desc = desc.format(sample_size/1000000.0,'M')
    elif sample_size >= 1000:
        desc = desc.format(sample_size /1000.0, 'K')
    else:
        desc = desc.format(sample_size, '')
    return desc


def process_row(bq_row):
    """
    Convert bq_row into dictionary and replace identifiers to nominal values

    Args:
        bq_row: BigQuery row

    Returns:
         dictionary

    """

    # modify opaque numeric race code into human-readable data
    races = dict(zip([1, 2, 3, 4, 5, 6, 7, 18, 28, 39, 48],
                     ['White', 'Black', 'American Indian', 'Chinese',
                      'Japanese', 'Hawaiian', 'Filipino',
                      'Asian bq_row', 'Korean', 'Samaon', 'Vietnamese']))
    instance = dict()

    instance['is_male'] = str(bq_row['is_male'])
    instance['mother_age'] = bq_row['mother_age']

    if 'mother_race' in bq_row and bq_row['mother_race'] in races:
        instance['mother_race'] = races[bq_row['mother_race']]
    else:
        instance['mother_race'] = 'Unknown'

    instance['plurality'] = bq_row['plurality']
    instance['gestation_weeks'] = bq_row['gestation_weeks']
    instance['mother_married'] = str(bq_row['mother_married'])
    instance['cigarette_use'] = str(bq_row['cigarette_use'])
    instance['alcohol_use'] = str(bq_row['alcohol_use'])
    instance['weight_pounds'] = str(bq_row['weight_pounds'])

    return instance


def to_json_line(bq_row):
    """
    Convert bq_row into json and replace identifiers to nominal values

    Args:
        bq_row: BigQuery row

    Returns:
         dictionary

    """

    # modify opaque numeric race code into human-readable data
    races = dict(zip([1, 2, 3, 4, 5, 6, 7, 18, 28, 39, 48],
                     ['White', 'Black', 'American Indian', 'Chinese',
                      'Japanese', 'Hawaiian', 'Filipino',
                      'Asian bq_row', 'Korean', 'Samaon', 'Vietnamese']))
    instance = dict()

    instance['is_male'] = str(bq_row['is_male'])
    instance['mother_age'] = bq_row['mother_age']

    if 'mother_race' in bq_row and bq_row['mother_race'] in races:
        instance['mother_race'] = races[bq_row['mother_race']]
    else:
        instance['mother_race'] = 'Unknown'

    instance['plurality'] = bq_row['plurality']
    instance['gestation_weeks'] = bq_row['gestation_weeks']
    instance['mother_married'] = str(bq_row['mother_married'])
    instance['cigarette_use'] = str(bq_row['cigarette_use'])
    instance['alcohol_use'] = str(bq_row['alcohol_use'])

    return json.dumps(instance)


def estimate(instance, inference_type):
    """
    Estimate the baby weight given an instance
    If inference type is 'cmle', the model API deployed on Coud ML Engine is called,
    otherwise, the local model is called

    Agrs:
        instance: dictionary of values representing the input features of the instance
        inference_type: cane be 'local or 'cmle'
    Returns:
         int - baby weight estimate from the model
    """

    # pop the actual weight if exists
    weight_pounds = instance.pop('weight_pounds', 'NA')

    if inference_type == 'local':
        estimated_weights = inference.estimate_local([instance])
    elif inference_type == 'cmle':
        estimated_weights = inference.estimate_cmle([instance])
    else:
        estimated_weights = 'NA'

    instance['estimated_weight'] = estimated_weights[0]
    instance['weight_pounds'] = weight_pounds[0]

    return instance


def to_csv(instance):
    """
    Convert the instance, including the estimated baby weight, to csv string

    Args:
        instance: dictionary of instance feature values and estimated target
    Returns:
        string: comma separated values
    """

    csv_row = ','.join([str(instance[k]) for k in HEADER])
    csv_row += ',{}'.format(instance['estimated_weight'])
    return csv_row


def run_pipeline(inference_type, sample_size, sink_location, runner, args=None):

    source_query = get_source_query(sample_size)

    sink_location = sink_location + "/data-estimates"

    sample_size_desc = get_sample_size_desc(sample_size)

    options = beam.pipeline.PipelineOptions(flags=[], **args)

    pipeline = beam.Pipeline(runner, options=options)

    (
            pipeline
            | 'Read from BigQuery {}'.format(sample_size_desc) >> beam.io.Read(beam.io.BigQuerySource(query=source_query, use_standard_sql=True))
            | 'Process BQ Row' >> beam.Map(process_row)
            | 'Estimate Targets - {}'.format(inference_type) >> beam.Map(lambda instance: estimate(instance, inference_type))
            | 'Convert to CSV' >> beam.Map(to_csv)
            | 'Write to Sink ' >> beam.io.Write(beam.io.WriteToText(sink_location, file_name_suffix='.csv'))
    )

    job = pipeline.run()
    if runner == 'DirectRunner':
        job.wait_until_finish()


def run_pipeline_with_batch_predict(sample_size, sink_location, runner, args=None):

    source_query = get_source_query(sample_size)

    sink_location = sink_location + "/data-prep"

    sample_size_desc = get_sample_size_desc(sample_size)

    options = beam.pipeline.PipelineOptions(flags=[], **args)

    pipeline = beam.Pipeline(runner, options=options)

    (
            pipeline
            | 'Read from BigQuery {}'.format(sample_size_desc) >> beam.io.Read(beam.io.BigQuerySource(query=source_query, use_standard_sql=True))
            | 'Convert to Json line' >> beam.Map(to_json_line)
            | 'Write to Sink ' >> beam.io.Write(beam.io.WriteToText(sink_location, file_name_suffix='.dat'))
    )

    job = pipeline.run()
    if runner == 'DirectRunner':
        job.wait_until_finish()
