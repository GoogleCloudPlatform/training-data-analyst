# imports
import apache_beam as beam
import google.cloud.ml as ml
import google.cloud.ml.analysis as analysis
import google.cloud.ml.io as io
import json
import os

OUTPUT_DIR='gs://cloud-training-demos-ml/landcover/prediction/'
import datetime
options = {
    'staging_location': os.path.join(OUTPUT_DIR, 'tmp', 'staging'),
    'temp_location': os.path.join(OUTPUT_DIR, 'tmp'),
    'job_name': 'evaluate' + '-' + datetime.datetime.now().strftime('%y%m%d-%H%M%S'),
    'project': 'cloud-training-demos',
    'extra_packages': [ml.sdk_location],
    'teardown_policy': 'TEARDOWN_ALWAYS',
    'max_num_workers': 10,
    'no_save_main_session': True
}
opts = beam.pipeline.PipelineOptions(flags=[], **options)
pipeline = beam.Pipeline('DataflowPipelineRunner', options=opts)

eval_features = (pipeline | 'ReadEval' >> io.LoadFeatures('gs://cloud-training-demos-ml/landcover/preproc/features_*')) # both eval & train
trained_model = pipeline | 'LoadModel' >> io.LoadModel('gs://cloud-training-demos-ml/landcover/trained/model')
evaluations = (eval_features | 'Evaluate' >> ml.Evaluate(trained_model) |
    beam.Map('ExtractEvaluationResults', lambda (example, prediction): prediction))
eval_data_sink = beam.io.TextFileSink(os.path.join(OUTPUT_DIR, 'eval'), shard_name_template='')
evaluations | beam.io.textio.WriteToText(os.path.join(OUTPUT_DIR, 'eval'), shard_name_template='')

# run pipeline
pipeline.run()
