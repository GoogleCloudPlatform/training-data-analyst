# Kaggle Competition Pipeline Sample

## Pipeline Overview

This is a pipeline for [house price prediction](https://www.kaggle.com/c/house-prices-advanced-regression-techniques), an entry-level competition in kaggle. We demonstrate how to complete a kaggle competition by creating a pipeline of steps including downloading data, preprocessing and visualizing data, train model and submitting results to kaggle website. 

* We refer to [the notebook by Raj Kumar Gupta](https://www.kaggle.com/rajgupta5/house-price-prediction) and [the notebook by Sergei Neviadomski](https://www.kaggle.com/neviadomski/how-to-get-to-top-25-with-simple-model-sklearn) in terms of model implementation as well as data visualization. 

* We use [kaggle python api](https://github.com/Kaggle/kaggle-api) to interact with kaggle site, such as downloading data and submiting result. More usage can be found in their documentation.

* We use [cloud build](https://cloud.google.com/cloud-build/) for CI process. That is, we automatically triggered a build and run as soon as we pushed our code to github repo. You need to setup a trigger on cloud build for your github repo branch to achieve the CI process.

## Notice
* You can authenticate to gcp services by either: Create a "user-gcp-sa" secret following the troubleshooting parts in [Kubeflow pipeline repo](https://github.com/kubeflow/pipelines/tree/master/manifests/kustomize), or configure workload identity as instructed in [this guide](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity). This sample uses the first method, but this will soon be deprecated. We would recommend using second method to replace the use of "user-gcp-sa" service account in the future.

## Usage

* Substitute the constants in "substitutions" in cloudbuild.yaml
* Fill in your kaggle_username and kaggle_key in Dockerfiles(in the folder "download_dataset" and "submit_result"） to authenticate to kaggle. You can get them from an API token created from your kaggle "My Account" page.
* Set up cloud build triggers to your github repo for Continuous Integration
* Replace the CLOUDSDK_COMPUTE_ZONE, CLOUDSDK_CONTAINER_CLUSTER in cloudbuild.yaml with your own zone and cluster
* Enable "Kubernetes Engine Developer" in cloud build setting
* Set your gs bucket public or grant cloud storage access to cloud build and kubeflow pipeline
* Try commit and push it to github repo