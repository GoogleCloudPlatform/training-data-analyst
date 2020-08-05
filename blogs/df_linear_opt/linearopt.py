#!/usr/bin/env python3

PROJECT = 'ai-analytics-solutions'
BUCKET = 'ai-analytics-solutions-kfpdemo'
REGION = 'us-central1'
INPUT = 'input.json'
RUNNER = 'DirectRunner'
OUTPUT = 'output.json'

# to try it with Dataflow, copy the file to your bucket and use DataflowRunner
if True:
    INPUT = 'gs://{}/linearopt/input.json'.format(BUCKET)
    RUNNER = 'DataflowRunner'
    OUTPUT = 'gs://{}/linearopt/output.json'.format(BUCKET)

# to try it in streaming mode, write one json message at a time to pub/sub
# and change the input to beam.io.ReadFromPubSub(topic=input_topic)
# and change the output to beam.io.WriteStringsToPubSub(output_topic)

from datetime import datetime
import apache_beam as beam

def linopt(materials):
    import numpy as np
    from scipy.optimize import linprog
    from scipy.optimize import OptimizeResult

    # coefficients of optimization function to *minimize*
    c = -1 * np.array([50, 100, 125, 40])
    # constraints  A_ub @x <= b_ub (could also use a_eq, b_eq, etc.)
    A_ub = [
        [50, 60, 100, 50],
        [5, 25, 10, 5],
        [300, 400, 800, 200],
        [30, 75, 50, 20]
    ]
    b_ub = [materials['dye'], materials['labor'], materials['water'], materials['concentrate']]
    bounds = [
        (0, np.inf),
        (0, 25),
        (0, 10),
        (0, np.inf)
    ]

    def log_info(status):
        print(status.nit, status.fun)

    print(b_ub)
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, callback=log_info)
    qty = np.round(res.x)
    print("{} --> {}".format(b_ub, qty))
    return qty

def run():
    import json

    options = beam.options.pipeline_options.PipelineOptions()
    setup_options = options.view_as(beam.options.pipeline_options.SetupOptions)
    #setup_options.requirements_file = 'requirements.txt'
    setup_options.save_main_session = True
    google_cloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
    google_cloud_options.project = PROJECT
    google_cloud_options.region = REGION
    google_cloud_options.job_name = 'linearopt-{}'.format(datetime.now().strftime("%Y%m%d-%H%M%S"))
    google_cloud_options.staging_location = 'gs://{}/staging'.format(BUCKET)
    google_cloud_options.temp_location = 'gs://{}/temp'.format(BUCKET)
    std_options = options.view_as(beam.options.pipeline_options.StandardOptions)
    std_options.runner = RUNNER

    p = beam.Pipeline(options=options)
    (p
      | 'ingest'    >> beam.io.ReadFromText(INPUT)
      | 'optimize'  >> beam.Map(lambda x : linopt(json.loads(x)))
      | 'output'    >> beam.io.WriteToText(OUTPUT)
    )
    result = p.run()
    result.wait_until_finish()

if __name__ == '__main__':
    run()
