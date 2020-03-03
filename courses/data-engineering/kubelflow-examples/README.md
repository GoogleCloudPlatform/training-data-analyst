# kubeflow-examples

A repository to share extended Kubeflow examples and tutorials to demonstrate machine learning
concepts, data science workflows, and Kubeflow deployments. The examples illustrate the happy path,
acting as a starting point for new users and a reference guide for experienced users.

This repository is home to the following types of examples and demos:
* [End-to-end](#end-to-end)
* [Component-focused](#component-focused)
* [Demos](#demos)

## End-to-end

### [Named Entity Recognition](./named_entity_recognition)
Author: [Sascha Heyer](https://github.com/saschaheyer)

This example covers the following concepts:
1. Build reusable pipeline components
2. Run Kubeflow Pipelines with Jupyter notebooks
1. Train a Named Entity Recognition model on a Kubernetes cluster
1. Deploy a Keras model to AI Platform
1. Use Kubeflow metrics
1. Use Kubeflow visualizations 

### [GitHub issue summarization](./github_issue_summarization)
Author: [Hamel Husain](https://github.com/hamelsmu)

This example covers the following concepts:
1. Natural Language Processing (NLP) with Keras and Tensorflow
1. Connecting to Jupyterhub
1. Shared persistent storage
1. Training a Tensorflow model
    1. CPU
    1. GPU
1. Serving with Seldon Core
1. Flask front-end

### [Pachyderm Example - GitHub issue summarization](./github_issue_summarization/Pachyderm_Example)
Author: [Nick Harvey](https://github.com/Nick-Harvey) & [Daniel Whitenack](https://github.com/dwhitena)

This example covers the following concepts:
1. A production pipeline for pre-processing, training, and model export
1. CI/CD for model binaries, building and deploying a docker image for serving in Seldon
1. Full tracking of what data produced which model, and what model is being used for inference
1. Automatic updates of models based on changes to training data or code
1. Training with single node Tensorflow and distributed TF-jobs

### [Pytorch MNIST](./pytorch_mnist)
Author: [David Sabater](https://github.com/dsdinter)

This example covers the following concepts:
1. Distributed Data Parallel (DDP) training with Pytorch on CPU and GPU
1. Shared persistent storage
1. Training a Pytorch model
    1. CPU
    1. GPU
1. Serving with Seldon Core
1. Flask front-end

### [MNIST](./mnist)

Author: [Elson Rodriguez](https://github.com/elsonrodriguez)

This example covers the following concepts:
1. Image recognition of handwritten digits
1. S3 storage
1. Training automation with Argo
1. Monitoring with Argo UI and Tensorboard
1. Serving with Tensorflow

### [Distributed Object Detection](./object_detection)

Author: [Daniel Castellanos](https://github.com/ldcastell)

This example covers the following concepts:
1. Gathering and preparing the data for model training using K8s jobs
1. Using Kubeflow tf-job and tf-operator to launch a distributed object training job
1. Serving the model through Kubeflow's tf-serving

### [Financial Time Series](./financial_time_series)

Author: [Sven Degroote](https://github.com/Svendegroote91)

This example covers the following concepts:
1. Deploying Kubeflow to a GKE cluster
2. Exploration via JupyterHub (prospect data, preprocess data, develop ML model)
3. Training several tensorflow models at scale with TF-jobs
4. Deploy and serve with TF-serving
5. Iterate training and serving
6. Training on GPU
7. Using Kubeflow Pipelines to automate ML workflow

### [Pipelines](./pipelines)

#### [Simple notebook pipeline](./pipelines/simple-notebook-pipeline)
Author: [Zane Durante](https://github.com/zanedurante)

This example covers the following concepts:
1. How to create pipeline components from python functions in jupyter notebook
2. How to compile and run a pipeline from jupyter notebook

#### [MNIST Pipelines](./pipelines/mnist-pipelines)
Author: [Dan Sanche](https://github.com/DanSanche) and [Jin Chi He](https://github.com/jinchihe)

This example covers the following concepts:
1. Run MNIST Pipelines sample on a Google Cloud Platform (GCP).
2. Run MNIST Pipelines sample for on premises cluster.

## Component-focused

### [XGBoost - Ames housing price prediction](./xgboost_ames_housing)
Author: [Puneith Kaul](https://github.com/puneith)

This example covers the following concepts:
1. Training an XGBoost model
1. Shared persistent storage
1. GCS and GKE
1. Serving with Seldon Core

## Demos

Demos are for showing Kubeflow or one of its components publicly, with the
intent of highlighting product vision, not necessarily teaching. In contrast,
the goal of the **examples** is to provide a self-guided walkthrough of
Kubeflow or one of its components, for the purpose of teaching you how to
install and use the product.

In an *example*, all commands should be embedded in the process and explained.
In a *demo*, most details should be done behind the scenes, to optimize for
 on-stage rhythm and limited timing.

You can find the demos in the [`/demos` directory](demos/).

## Third-party hosted

| Source | Example | Description |
| ------ | ------- | ----------- |
| | | | |

## Get Involved

* [Slack](https://join.slack.com/t/kubeflow/shared_invite/enQtNDg5MTM4NTQyNjczLWUyZGI1ZmExZWExYWY4YzlkOWI4NjljNjJhZjhjMjEwNGFjNmVkNjg2NTg4M2I0ZTM5NDExZWI5YTIyMzVmNzM)
* [Twitter](http://twitter.com/kubeflow)
* [Mailing List](https://groups.google.com/forum/#!forum/kubeflow-discuss)

In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to making participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

The Kubeflow community is guided by our [Code of Conduct](https://github.com/kubeflow/community/blob/master/CODE_OF_CONDUCT.md), which we encourage everybody to read before participating.
