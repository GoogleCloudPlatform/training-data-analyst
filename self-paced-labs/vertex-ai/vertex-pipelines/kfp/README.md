# Vertex Pipelines: Chicago taxifare tip prediction using AutoML Tables and Kubeflow Pipelines SDK

This lab shows how to use the Kubeflow SDK pre-built and custom components to build an AutoML Tables workflow on Vertex Pipelines for .

## Learning objectives

1. Perform exploratory data analysis (EDA) on tabular data using BigQuery.
2. Create a BigQuery dataset for a ML classification task.
3. Define an AutoML tables pipeline using the Kubeflow Pipelines (KFP) SDK for model training, evaluation, and conditional deployment.
4. Create a custom model evaluation component using the KFP SDK.
5. Incorporate pre-built KFP components into your pipeline from `google_cloud_components`.
6. Query your model for online predictions and explanations. 

## Setup

1. Create service accounts for Vertex Training and Vertex Pipelines
1. Open a Terminal
1. Clone the repository to your Vertex Notebook instance:
1. Install the required Python packages:
1. Update the `gcloud` components


## Dataset

The [Chicago Taxi Trips](https://pantheon.corp.google.com/marketplace/details/city-of-chicago-public-data/chicago-taxi-trips) dataset is one of the [public datasets hosted with BigQuery](https://cloud.google.com/bigquery/public-data/), which includes taxi trips from 2013 to the present, reported to the City of Chicago in its role as a regulatory agency. The task is to predict whether a given trip will result in a tip > 20%.

## License

Copyright 2021 Google LLC.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
