# Vertex AI: Qwikstart

In this lab, you will walk through an introductory, end-to-end training and deployment workflow for a custom container TensorFlow model on Vertex AI.

## Learning objectives

* Train a TensorFlow model locally in a hosted [**Vertex Notebook**](https://cloud.google.com/vertex-ai/docs/general/notebooks?hl=sv).
* Create a [**managed Tabular dataset**](https://cloud.google.com/vertex-ai/docs/training/using-managed-datasets?hl=sv) artifact for experiment tracking.
* Containerize your training code with [**Cloud Build**](https://cloud.google.com/build) and push it to [**Google Cloud Container Registry**](https://cloud.google.com/container-registry).
* Run a [**Vertex AI custom training job**]() with your custom model container.
* Use [**Vertex TensorBoard**](https://cloud.google.com/vertex-ai/docs/experiments/tensorboard-overview) to visualize model performance.
* Deploy your trained model to a [**Vertex Prediction Endpoint**](https://cloud.google.com/vertex-ai/docs/predictions/getting-predictions) for serving predictions.
* Request an online prediction and see the response.

## Setup

To enable Cloud Services utilized in the lab environment:

1. Launch [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell)
2. Set your project ID
```
PROJECT_ID=[YOUR PROJECT ID]

gcloud config set project $PROJECT_ID
```
3. Use `gcloud` to enable the services
```
gcloud services enable \
compute.googleapis.com \
iam.googleapis.com \
cloudbuild.googleapis.com \
container.googleapis.com \
notebooks.googleapis.com \
aiplatform.googleapis.com \
dataflow.googleapis.com \
bigquery.googleapis.com \
bigquerydatatransfer.googleapis.com \  
artifactregistry.googleapis.com \
cloudresourcemanager.googleapis.com \
cloudtrace.googleapis.com \
iamcredentials.googleapis.com \
monitoring.googleapis.com \
logging.googleapis.com
```

## Creating a Vertex Notebooks instance

An instance of **Vertex Notebooks** is used as a primary lab environment.

To provision the instance follow the [Create an new notebook instance](https://cloud.google.com/vertex-ai/docs/general/notebooks) setup guide. Use the *TensorFlow Enterprise 2.3* no-GPU image. Leave all other settings at their default values.

After the instance is created, you can connect to [JupyterLab](https://jupyter.org/) IDE by clicking the *OPEN JUPYTERLAB* link in the [Vertex AI Notebooks Console](https://console.cloud.google.com/vertex-ai/notebooks/instances).

In the **JupyterLab**, open a terminal and clone this repository in the `home` folder.
```
cd
git clone https://github.com/GoogleCloudPlatform/training-data-analyst.git
```

Navigate to the lab folder and happy coding.

```
cd training-data-analyst/tree/master/self-paced-labs/vertex-ai/vertex-ai-qwikstart
```