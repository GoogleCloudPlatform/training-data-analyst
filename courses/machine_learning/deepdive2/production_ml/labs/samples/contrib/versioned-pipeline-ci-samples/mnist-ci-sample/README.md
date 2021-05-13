# Mnist Continuous Integration(CI) Pipeline

## Overview

This sample uses cloud build to implement the continuous integration process of a basic machine learning pipeline that trains and visualizes model in tensorboard. Once all set up, you can push your code to github repo, then the build process in cloud build will be triggered automatically, then a run will be created in kubeflow pipeline. You can view your pipeline and the run in kubeflow pipelines. 

We use **Kubeflow Pipeline(KFP) SDK** to interact with kubeflow pipeline to create a new version and a run in this sample.

## What you can learn in this sample
* CI process of a simple but general ML pipeline.
* Launch a tensorboard as one pipeline step
* Data passing between steps


## What needs to be done before run
* Authenticate to gcp services by either: Create a "user-gcp-sa" secret following the troubleshooting parts in [KFP Repo](https://github.com/kubeflow/pipelines/tree/master/manifests/kustomize), or configure workload identity as instructed in [this guide](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity). This sample uses the first method, but this will soon be deprecated. Please refer to the second method to replace the use of "user-gcp-sa" service account.
* Set up a trigger in cloud build, and link it to your github repo
* Enable "Kubernetes Engine Developer" in cloud build setting
* Replace the CLOUDSDK_COMPUTE_ZONE, CLOUDSDK_CONTAINER_CLUSTER in cloudbuild.yaml with your own zone and cluster
* Substitute the 'substitution' field in cloudbuild.yaml:

`_GCR_PATH`: '[YOUR CLOUD REGISTRY], for example: gcr.io/my-project' \
`_GS_BUCKET`: '[YOUR GS BUCKET TO STORE PIPELINE AND LAUNCH TENSORBOARD], for example: gs://my-bucket'\
`_PIPELINE_ID`: '[PIPELINE ID TO CREATE A VERSION ON], get it on kfp UI' \

* Set your container registy public or grant cloud registry access to cloud build and kubeflow pipeline
* Set your gs bucket public or grant cloud storage access to cloud build and kubeflow pipeline
* Try a commit to your repo, then you can observe the build process triggered automatically 



