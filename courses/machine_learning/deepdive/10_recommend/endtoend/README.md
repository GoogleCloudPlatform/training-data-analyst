# Recommendations on GCP with TensorFlow and WALS

This project deploys a solution for a recommendation service on GCP, using the WALS
algorithm in TensorFlow.  Components include:

- Recommendation model code, and scripts to train and tune the model on ML Engine
- A REST endpoint using [Google Cloud Endpoints](https://cloud.google.com/endpoints/) for serving recommendations
- An Airflow server managed by Cloud Composer (or alternatively, running on GKE) for running scheduled model training


## Steps

- open endtoend.ipynb and complete the one-time architecture setup
- copy airflow/dags/ and airflow/plugins to your corresponding Cloud Composer bucket
