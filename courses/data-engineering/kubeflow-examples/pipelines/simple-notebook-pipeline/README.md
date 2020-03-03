# Simple Notebook Pipeline on GCP
This notebook shows how to compile and run a simple Kubeflow pipeline using Jupyter notebooks and Google Cloud Storage.  The pipeline is very simple, and is a helpful starting point for people new to Kubeflow.

## Setup

### Setup notebook server
This pipeline requires you to [setup a notebook server](https://www.kubeflow.org/docs/notebooks/setup/) in the Kubeflow UI.  After you are setup, upload this notebook and then run it in the notebook server.

### Upload the notebook to the Kubeflow UI
In order to run this pipeline, make sure to upload the notebook to your notebook server in the Kubeflow UI.  You can clone this repo in the Jupyter notebook server by connecting to the notebook server and then selecting New > Terminal.  In the terminal type `git clone https://github.com/kubeflow/examples.git`.