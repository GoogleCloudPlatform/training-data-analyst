import os
import shutil
import logging
from pipelines import batch_process, stream_process
from datetime import datetime
import experiment
import argparse


def run_experiment(args):

    if experiment.PARAMS.experiment_type == 'batch':

        batch_process.run_pipeline(inference_type=experiment.PARAMS.inference_type,
                                   sample_size=experiment.PARAMS.batch_size,
                                   sink_location=experiment.PARAMS.sink_dir,
                                   runner=experiment.PARAMS.runner,
                                   args=args)

    elif experiment.PARAMS.experiment_type == 'batch-predict':

        batch_process.run_pipeline_with_batch_predict(sample_size=experiment.PARAMS.batch_sample_size,
                                                      sink_location=experiment.PARAMS.sink_dir,
                                                      runner=experiment.PARAMS.runner,
                                                      args=args
        )

    elif experiment.PARAMS.experiment_type == 'stream':

        stream_process.run_pipeline(inference_type=experiment.PARAMS.inference_type,
                                    project=experiment.PARAMS.project_id,
                                    pubsub_topic=experiment.PARAMS.pubsub_topic,
                                    pubsub_subscription=experiment.PARAMS.pubsub_subscription,
                                    bq_dataset=experiment.PARAMS.bq_dataset,
                                    bq_table=experiment.PARAMS.bq_table,
                                    runner=experiment.PARAMS.runner,
                                    args=args)

    elif experiment.PARAMS.experiment_type == 'stream-m-batches':

        stream_process.run_pipeline_with_micro_batches(inference_type=experiment.PARAMS.inference_type,
                                    project=experiment.PARAMS.project_id,
                                    pubsub_topic=experiment.PARAMS.pubsub_topic,
                                    pubsub_subscription=experiment.PARAMS.pubsub_subscription,
                                    bq_dataset=experiment.PARAMS.bq_dataset,
                                    bq_table=experiment.PARAMS.bq_table,
                                    window_size=experiment.PARAMS.window_size,
                                    runner=experiment.PARAMS.runner,
                                    args=args)


if __name__ == '__main__':

    args_parser = argparse.ArgumentParser()
    experiment.initialise_hyper_params(args_parser)

    print ''
    print 'Experiment Parameters:'
    print experiment.PARAMS
    print ''

    if experiment.PARAMS.runner == 'DirectRunner':
        shutil.rmtree(experiment.PARAMS.sink_dir, ignore_errors=True)

    job_name = 'tf-predict-{}-{}-{}'.format(experiment.PARAMS.inference_type,
                                            experiment.PARAMS.experiment_type,
                                            datetime.now().strftime('%Y%m%d-%H%M%S')
                                            )

    print('Launching Beam job {} - {} ... hang on'.format(experiment.PARAMS.runner, job_name))

    dataflow_args = {
        'region': 'europe-west1',
        'staging_location': os.path.join(experiment.PARAMS.sink_dir, 'tmp', 'staging'),
        'temp_location': os.path.join(experiment.PARAMS.sink_dir, 'tmp'),
        'job_name': job_name,
        'project': experiment.PARAMS.project_id,
        'num_workers': 5, # set to fix number of workers and disable autoscaling
        #'max_num_workers': 20,
        'setup_file': './setup.py',
        'streaming': experiment.PARAMS.experiment_type in ['stream', 'stream-m-batches'],
    }

    logging.getLogger().setLevel(logging.INFO)

    time_start = datetime.utcnow()
    print("Job started at {}".format(time_start.strftime('%Y-%m-%d %H:%M:%S')))
    print(".......................................")

    run_experiment(dataflow_args)

    time_end = datetime.utcnow()
    print(".......................................")
    print("Job finished at {}".format(time_end.strftime('%Y-%m-%d %H:%M:%S')))
    print("")
    time_elapsed = time_end - time_start
    print("Job elapsed time: {} seconds".format(time_elapsed.total_seconds()))
