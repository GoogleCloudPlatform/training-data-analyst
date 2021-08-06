# Deploy a BQML customer churn classifier to Vertex AI for online prediction

In this lab, you will train, evaluate, and explain a BQML model for predicting customer churn. You will then deploy it to Vertex AI for serving online predictions.

## Learning objectives

* Train a BQML classifier to predict customer churn.
* Evaluate the performance of a BQML classifier.
* Explain your model with BQML Explainable AI.
* Export a BQML model to Vertex AI for online predictions.

## Setup

### 1. Enable Cloud Services utilized in the lab environment:

#### 1.1 Launch [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell)

#### 1.2 Set your Project ID

Confirm that you see the desired project ID returned below:
```
gcloud config get-value project
```

If you do not see your desired project ID, set it as follows:
```
PROJECT_ID=[YOUR PROJECT ID]
gcloud config set project $PROJECT_ID
```

#### 1.3 Use `gcloud` to enable the services

```
gcloud services enable \
  compute.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  notebooks.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
```

### 2. Creating a Vertex Notebooks instance

An instance of **Vertex Notebooks** is used as a primary lab environment.

To provision the instance follow the [Create an new notebook instance](https://cloud.google.com/vertex-ai/docs/general/notebooks) setup guide. Use the *TensorFlow Enterprise 2.3* no-GPU image. Leave all other settings at their default values.

After the instance is created, you can connect to [JupyterLab](https://jupyter.org/) IDE by clicking the *OPEN JUPYTERLAB* link in the [Vertex AI Notebooks Console](https://console.cloud.google.com/vertex-ai/notebooks/instances).


### 4. Clone the lab repository

In your **JupyterLab** instance, open a terminal and clone this repository in the `home` folder.
```
cd
git clone https://github.com/GoogleCloudPlatform/training-data-analyst.git
```

### 5. Install the lab dependencies

Run the following in the **JupyterLab** terminal to go to the `training-data-analyst/self-paced-labs/vertex-ai/vertex-bqml` folder, then pip install `requirements.txt` to install lab dependencies:

```bash
cd training-data-analyst/self-paced-labs/vertex-ai/vertex-bqml
pip install -U -r requirements.txt
```

### 6. Navigate to lab notebook

In your **JupyterLab** instance, navigate to __training-data-analyst__ > __self-paced-labs__ > __vertex-ai__ > __vertex-bqml__, and open __lab_exercise.ipynb__.

Open `lab_exercise.ipynb` to complete the lab. 

Happy coding!