# TFX Pipeline Example

This sample walks through running [TFX](https://github.com/tensorflow/tfx) [Taxi Application Example](https://github.com/tensorflow/tfx/tree/master/tfx/examples/chicago_taxi_pipeline) on Kubeflow Pipelines cluster. 

## Overview

This pipeline demonstrates the TFX capabilities at scale. The pipeline uses a public BigQuery dataset and uses GCP services to preprocess data (Dataflow) and train the model (Cloud ML Engine). The model is then deployed to Cloud ML Engine Prediction service.


## Setup

Enable DataFlow API for your GKE cluster: <https://console.developers.google.com/apis/api/dataflow.googleapis.com/overview>

Create a local Python 3.5 conda environment
```
conda create -n tfx-kfp pip python=3.5.3
```
then activate the environment.


Install TFX and Kubeflow Pipelines SDK
```
pip3 install 'tfx==0.14.0' --upgrade
pip3 install 'kfp>=0.1.31' --upgrade
```

Upload the utility code to your storage bucket. You can modify this code if needed for a different dataset.
```
gsutil cp utils/taxi_utils.py gs://my-bucket/<path>/
```

If gsutil does not work, try `tensorflow.gfile`:
```
from tensorflow import gfile
gfile.Copy('utils/taxi_utils.py', 'gs://<my bucket>/<path>/taxi_utils.py')
```

## Configure the TFX Pipeline

Modify the pipeline configurations at
```
TFX Example.ipynb
```
Configure
- Set `_input_bucket` to the GCS directory where you've copied taxi_utils.py. I.e. gs://<my bucket>/<path>/
- Set `_output_bucket` to the GCS directory where you've want the results to be written
- Set GCP project ID (replace my-gcp-project). Note that it should be project ID, not project name.
- The original BigQuery dataset has 100M rows, which can take time to process. Modify the selection criteria (% of records) to run a sample test. 

## Compile and run the pipeline
Run the notebook.

This will generate a file named `chicago_taxi_pipeline_kubeflow.tar.gz`.
Upload this file to the Pipelines Cluster and create a run.
