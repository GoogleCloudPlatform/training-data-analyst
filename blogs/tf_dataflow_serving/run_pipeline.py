import os
import shutil
import logging
from pipelines import batch_process, stream_process
from datetime import datetime


SAMPLE_SIZE = 100000

EXPERIMENT = 'stream-m-batches'  # batch | stream-m-batches | stream | batch-predict

RUNNER = 'DataflowRunner'  # 'DirectRunner' | 'DataflowRunner'
PROJECT = 'ksalama-gcp-playground'
BUCKET = 'ksalama-gcs-cloudml'
INFERENCE_TYPE = 'cmle'  # local'| 'cmle' | 'None'
PUBSUB_TOPIC='babyweights'


local_dir = 'local_data'
gcs_dir = 'gs://{0}/data/babyweight/tf-data-out'.format(BUCKET)

output_dir = local_dir if RUNNER == 'DirectRunner' else gcs_dir

sink_location = os.path.join(output_dir, 'data-estimates')

pubsub_topic = "projects/{}/topics/{}".format(PROJECT, PUBSUB_TOPIC)

shutil.rmtree(output_dir, ignore_errors=True)

job_name = 'tf-predict-{}-{}-{}'.format(INFERENCE_TYPE, EXPERIMENT,datetime.now().strftime('%y%m%d-%H%M%S'))
print('Launching Beam job {} - {} ... hang on'.format(RUNNER, job_name))


args = {
    #'region': 'europe-west1',
    'staging_location': os.path.join(gcs_dir, 'tmp', 'staging'),
    'temp_location': os.path.join(gcs_dir, 'tmp'),
    'job_name': job_name,
    'project': PROJECT,
    'teardown_policy': 'TEARDOWN_ALWAYS',
    'no_save_main_session': True,
    'setup_file': './setup.py',
    'streaming': EXPERIMENT in ['stream','stream-m-batches'],
}


if __name__ == '__main__':

    logging.getLogger().setLevel(logging.INFO)

    time_start = datetime.utcnow()
    print("Job started at {}".format(time_start.strftime("%H:%M:%S")))
    print(".......................................")

    if EXPERIMENT == 'batch':
        batch_process.run_pipeline(inference_type=INFERENCE_TYPE,
                                   sample_size=SAMPLE_SIZE,
                                   sink_location=sink_location,
                                   runner=RUNNER,
                                   args=args)

    elif EXPERIMENT == 'batch-predict':
        batch_process.run_pipeline_with_batch_predict(
                               sample_size=SAMPLE_SIZE,
                               sink_location=sink_location,
                               runner=RUNNER,
                               args=args)

    elif EXPERIMENT == 'stream':
        stream_process.run_pipeline(inference_type=INFERENCE_TYPE,
                                    pubsub_topic=pubsub_topic,
                                    runner='DataflowRunner',
                                    args=args)

    elif EXPERIMENT == 'stream-m-batches':
        stream_process.run_pipeline_with_micro_batches(inference_type=INFERENCE_TYPE,
                                    pubsub_topic=pubsub_topic,
                                    runner='DataflowRunner',
                                    args=args)

    time_end = datetime.utcnow()
    print(".......................................")
    print("Job finished at {}".format(time_end.strftime("%H:%M:%S")))
    print("")
    time_elapsed = time_end - time_start
    print("Job elapsed time: {} seconds".format(time_elapsed.total_seconds()))