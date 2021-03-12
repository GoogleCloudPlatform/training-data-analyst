## Overview

The `xgboost_training_cm.py` pipeline creates XGBoost models on structured data in CSV format. Both classification and regression are supported.

The pipeline starts by creating a Google DataProc cluster, and then running analysis, transformation, distributed training and 
prediction in the created cluster. 
Then a single node confusion-matrix and ROC aggregator is used (for classification case) to	
provide the confusion matrix data, and ROC data to the front end, respectively.
Finally, a delete cluster operation runs to destroy the cluster it creates
in the beginning. The delete cluster operation is used as an exit handler, meaning it will run regardless of whether the pipeline fails
or not.

## Requirements

> :warning: If you are using **full-scope** or **workload identity enabled** cluster in hosted pipeline beta version, **DO NOT** follow this section. However you'll still need to enable corresponding GCP API.

Preprocessing uses Google Cloud DataProc. Therefore, you must enable the 
[Cloud Dataproc API](https://pantheon.corp.google.com/apis/library/dataproc.googleapis.com?q=dataproc) for the given GCP project. This is the 
general [guideline](https://cloud.google.com/endpoints/docs/openapi/enable-api) for enabling GCP APIs.
If KFP was deployed through K8S marketplace, please follow instructions in [the guideline](https://github.com/kubeflow/pipelines/blob/master/manifests/gcp_marketplace/guide.md#gcp-service-account-credentials)
to make sure the service account used has the role `storage.admin` and `dataproc.admin`.

### Quota

By default, Dataproc `create_cluster` creates a master instance of machine type 'n1-standard-4',
together with two worker instances of machine type 'n1-standard-4'. This sums up
to a request consuming 12.0 vCPU quota. The user GCP project needs to guarantee
this quota is available to make this sample work.

> :warning: Free-tier GCP account might not be able to fulfill this quota requirement. For upgrading your account please follow [this link]().

## Compile

Follow the guide to [building a pipeline](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/) to install the Kubeflow Pipelines SDK and compile the sample Python into a workflow specification. The specification takes the form of a YAML file compressed into a `.zip` file. 

## Deploy

Open the Kubeflow pipelines UI. Create a new pipeline, and then upload the compiled specification (`.zip` file) as a new pipeline template.

## Run

All arguments come with default values. This pipeline is preloaded as a Demo pipeline in Pipeline UI. You can run the pipeline without any changes.

## Modifying the pipeline
To do additional exploration you may change some of the parameters, or pipeline input that is currently specified in the pipeline definition.  
 
* `output` is a Google Storage path which holds pipeline run results.
Note that each pipeline run will create a unique directory under `output` so it will not override previous results.
* `workers` is number of worker nodes used for this training. 
* `rounds` is the number of XGBoost training iterations. Set the value to 200 to get a reasonable trained model.
* `train_data` points to a CSV file that contains the training data. For a sample see 'gs://ml-pipeline-playground/sfpd/train.csv'.
* `eval_data` points to a CSV file that contains the training data. For a sample see 'gs://ml-pipeline-playground/sfpd/eval.csv'.
* `schema` points to a schema file for train and eval datasets. For a sample see 'gs://ml-pipeline-playground/sfpd/schema.json'.

## Components source

Create Cluster:
  [source code](https://github.com/kubeflow/pipelines/blob/master/components/gcp/container/component_sdk/python/kfp_component/google/dataproc/_create_cluster.py) 

Analyze (step one for preprocessing), Transform (step two for preprocessing) are using pyspark job
submission component, with
  [source code](https://github.com/kubeflow/pipelines/blob/master/components/gcp/container/component_sdk/python/kfp_component/google/dataproc/_submit_pyspark_job.py) 

Distributed Training and predictions are using spark job submission component, with
  [source code](https://github.com/kubeflow/pipelines/blob/master/components/gcp/container/component_sdk/python/kfp_component/google/dataproc/_submit_spark_job.py) 

Delete Cluster:
  [source code](https://github.com/kubeflow/pipelines/blob/master/components/gcp/container/component_sdk/python/kfp_component/google/dataproc/_delete_cluster.py) 

The container file is located [here](https://github.com/kubeflow/pipelines/tree/master/components/gcp/container) 

For visualization, we use confusion matrix and ROC.
Confusion Matrix:	
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/local/confusion_matrix/src),
  [container](https://github.com/kubeflow/pipelines/tree/master/components/local/confusion_matrix)
and ROC: 
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/local/roc/src), 
  [container](https://github.com/kubeflow/pipelines/tree/master/components/local/roc)

