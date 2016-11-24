def make_data_for_analysis(values, metadata):
    import numpy as np
    lookup = metadata['columns']['landcover']['vocab']
    return {
      'target': lookup[values['target']],
      'predicted': lookup[values['label']],
      'score': np.max(values['score']), # not needed
    }

def read_metadata(gcsfile):
    import subprocess
    filename = '/tmp/metadata.yaml'
    subprocess.check_output(['gsutil', 'cp', gcsfile, filename])
    import yaml
    with open(filename, 'r') as stream:
      try:
        return yaml.load(stream)
      except yaml.YAMLError as exc:
        print(exc)

def create_confusion_matrix():
  # imports
  import apache_beam as beam
  import google.cloud.ml as ml
  import google.cloud.ml.analysis as analysis
  import google.cloud.ml.io as io
  import json
  import os
  import numpy as np
  
  OUTPUT_DIR = 'gs://cloud-training-demos-ml/landcover/prediction/confusion'
  BUCKET = 'cloud-training-demos-ml'
  PROJECT = 'cloud-training-demos'
  INPUT = 'gs://cloud-training-demos-ml/landcover/prediction/eval*'
  RUNNER = 'DataflowPipelineRunner' 
  pipeline = beam.Pipeline(argv=['--project', PROJECT,
                               '--runner', RUNNER,
                               '--job_name', 'landcover-confusion-matrix',
                               '--extra_package', ml.sdk_location,
                               '--max_num_workers', '100',
                               '--save_main_session', 'True',
                               '--setup_file', './preproc/setup.py',  # for gdal installation on the cloud -- see CUSTOM_COMMANDS in setup.py
                               '--staging_location', 'gs://{0}/landcover/staging'.format(BUCKET),
                               '--temp_location', 'gs://{0}/landcover/temp'.format(BUCKET)])


  metadata_file = 'gs://cloud-training-demos-ml/landcover/trained/model/metadata.yaml'
  metadata_inmem = read_metadata(metadata_file)
  metadata = pipeline | io.LoadMetadata(metadata_file)
  evaluations = pipeline | beam.Read(beam.io.TextFileSource('gs://cloud-training-demos-ml/landcover/prediction/eval'))
 
  analysis_source = evaluations | beam.Map('CreateAnalysisSource', lambda v : make_data_for_analysis(v, metadata_inmem))
  confusion_matrix, precision_recall, logloss = (analysis_source |
    'Analyze Model' >> analysis.AnalyzeModel(metadata))
  confusion_matrix_file = os.path.join(OUTPUT_DIR, 'analyze_cm.json')
  confusion_matrix_sink = beam.io.TextFileSink(confusion_matrix_file, shard_name_template='')
  confusion_matrix | beam.io.Write('WriteConfusionMatrix', confusion_matrix_sink)

  # run pipeline
  pipeline.run()
  
create_confusion_matrix()
