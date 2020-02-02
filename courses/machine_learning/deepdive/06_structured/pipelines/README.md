# How to create and deploy a Kubeflow Machine Learning Pipeline (Part 1)

To repeat the steps in the article, follow these steps.

## Start Hosted Pipelines
Create Hosted Kubeflow Pipelines Instance

* Navigate to https://console.cloud.google.com/marketplace/details/google-cloud-ai-platform/kubeflow-pipelines
* Make sure your GCP project is selected in the dropdown at the top.
* Click CONFIGURE
* Change the App Instance Name to “kfpdemo”
* Click on the Create Cluster button and wait 2-3 minutes for cluster to get created.
* Click Deploy
* Navigate to https://console.cloud.google.com/ai-platform/pipelines/clusters
* Click on the HOSTED PIPELINES DASHBOARD LINK for kfpdemo on the cluster that you just started.

## Give the cluster permissions to run BigQuery, Dataflow, etc.

In CloudShell:
Run:
```
git clone https://github.com/GoogleCloudPlatform/training-data-analyst
cd training-data-analyst/courses/machine_learning/deepdive/06_structured/pipelines
./setup_auth.sh kfpdemo us-central1-a cluster-1 default
```
* The first parameter is the service account you are using. I'm calling it kfpdemo
* The next three parameters are the zone, cluster, and namespace of the Kubeflow cluster -- you can find the cluster details at https://console.cloud.google.com/ai-platform/pipelines/clusters
* Check the service account IAM permissions at https://console.cloud.google.com/iam-admin/iam ; you can add other necessary permissions there.


## Launch AI Platform notebook
Create Notebooks instance
* Navigate to https://console.cloud.google.com/ai-platform/notebooks/instances
* Click on +New Instance and create a TensorFlow 2.x notebook
* Name the instance kfpdemo
* Click Customize 
  * In Machine Configuration, change it to n1-standard-2
  * In Permissions, change access to "Other service account" and specify kfpdemo@PROJECT_ID.iam.gserviceaccount.com (specify your project id)
  * Click Create
* Click on the URL for Open JupyterLab
* Open a Terminal
* Type:
    ```git clone https://github.com/GoogleCloudPlatform/training-data-analyst```

## Navigate to notebook
* On the left-hand side menu, navigate to this notebook (training-data-analyst/courses/machine_learning/deepdive/06_structured/7_pipelines.ipynb)
* Run the cells in that notebook
