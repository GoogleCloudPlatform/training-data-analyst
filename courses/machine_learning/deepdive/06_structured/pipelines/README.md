# How to create and deploy a Kubeflow Machine Learning Pipeline (Part 1)

To repeat the steps in the article, follow these steps.

## Setup
* Run `./create_cluster.sh`
* Watch [GKE section of the GCP console](https://console.cloud.google.com/kubernetes) and make sure cluster is created.
* Run `./2_deploy_kubeflow_pipelines.sh`
* Install the local interpreter: `./3_install_sdk.sh`

## Build the Docker containers
* Examine the following code:
  * the pipeline code in `mlp_babyweight.py`
  * the files in `containers/bqtocsv`
* Build the containers using `cd containers; ./build_all.sh`
  
## Run the pipeline
* Edit mlp_babyweight.py to reflect the project that the containers belong to. In your favorite text editor, do a search-and-replace of `cloud-training-demos` to your project name (the container name has to be a static string).
* Do the DSL compile: `dsl-compile --py mlp_babyweight.py --output mlp_babyweight.tar.gz`
* Start the UI: `./4_start_ui.sh`
* Navigate to https://localhost:8085/
* Upload the pipeline
* Create an experiment
* Create a run of the pipeline, changing project and bucket as necessary
* Monitor the logs
