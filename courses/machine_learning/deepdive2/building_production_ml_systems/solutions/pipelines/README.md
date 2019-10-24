# Taxifare Kubeflow Pipeline

## Assumptions

The pipeline takes a single input, the Google Cloud Storage bucket where it will
create the training and evaluation datasets, as well as export the trained model.

The data will be stored at
```bash
gs://<BUCKET>/taxifare/data/taxi-train*.csv
gs://<BUCKET>/taxifare/data/taxi-valid*.csv
```

The model will be stored at 
```bash
gs://<BUCKET/taxifare/model
```

The training takes place on the AI-platform and assumes
that the training container (`taxifare-trainer`) Docker image
has been already exported to the project Docker registry.
(This should have been done by completing the previous lab, or by 
running `make` in `../taxifare`.)


The model will be deployed on the AI-platform with name `taxifare` and
version `dnn`.

The training parameters can be modified in the training submission
script `./components/trainjob/main.sh`. For simplicity, we do not
surface these parameters to the Kubeflow UI dashboard.  


## Pre-requisite

A [Kubeflow](https://www.kubeflow.org/) cluster needs to be deployed
in your GCP project, using the [Kubeflow cluster deployment](https://deploy.kubeflow.cloud/#/deploy).
There is a [setup video](https://www.kubeflow.org/docs/started/cloud/getting-started-gke/~) that will
take you over all the steps in details, and explains how to access to the Kubeflow Dashboard UI, once it is 
running. 

You'll need to create an OAuth client for authentication purposes: Follow the 
instructions [here](https://www.kubeflow.org/docs/gke/deploy/oauth-setup/).

## Building the pipeline

The pipeline has three components:

* `./components/bq2gcs` that creates the training and evaluation data from BigQuery and export it to GCS
* `./components/trainjob` that launches the training container on AI-platform and export the model
* `./components/deploymodel` that deploys the trained model to AI-platform as a REST API

To build the pipeline type

```bash
$ make
```

This will 
1. go recursively into each of the compoment subdirectory, build their Docker images, and push them into the gcr.io registry
2. build the pipeline artifact `taxifare.tar.gz` that you'll need to uploaed into the Kubeflow Pipeline UI to run it.


## Uploading the pipline

Read the instructions [here](https://www.kubeflow.org/docs/gke/pipelines-tutorial/) to understand how to upload
and run the pipeline artifact `taxifare.tar.gz`.
