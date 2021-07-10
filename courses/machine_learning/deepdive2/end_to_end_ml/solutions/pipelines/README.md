# How to create and deploy a Kubeflow Machine Learning Pipeline (Part 1)
See:
https://towardsdatascience.com/how-to-create-and-deploy-a-kubeflow-machine-learning-pipeline-part-1-efea7a4b650f

To repeat the steps in the article, follow these steps.

## 1. Set up Hosted Kubeflow Pipelines

You will use a Kubernetes cluster to run the ML Pipelines.

### 1a. Start Hosted Pipelines
Create Hosted Kubeflow Pipelines Instance

* From the GCP Console, navigate to AI Platform | Pipelines and select +New Instance or browse directly to https://console.cloud.google.com/marketplace/details/google-cloud-ai-platform/kubeflow-pipelines
* Make sure your GCP project is selected in the dropdown at the top.
* Click CONFIGURE
* Change the App Instance Name to “kfpdemo”
* Click on the Create Cluster button and wait 2-3 minutes for cluster to get created.
* Click Deploy
* Navigate to https://console.cloud.google.com/ai-platform/pipelines/clusters
* Click on the HOSTED PIPELINES DASHBOARD LINK for kfpdemo on the cluster that you just started.

### 1b. Give the cluster permissions to run BigQuery, Dataflow, etc.

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


## 2. Development environment

You will use AI Platform Notebooks to develop and deploy the code to Kubeflow Pipelines.

### 2a. Launch AI Platform notebook
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

### 2b. Navigate to notebook for development workflow
* On the left-hand side menu, navigate to this notebook (training-data-analyst/courses/machine_learning/deepdive/06_structured/7_pipelines.ipynb)
* Change the pipelines host in the notebook to reflect the URL of your KFP installation
* Run the cells in that notebook to deploy the pipeline manually.


# How to carry out CI/CD in Machine Learning ("MLOps") using Kubeflow ML Pipelines (Part 3)
See:
https://medium.com/@lakshmanok/how-to-carry-out-ci-cd-in-machine-learning-mlops-using-kubeflow-ml-pipelines-part-3-bdaf68082112

## 3. CI/CD Production Environment

### 3a Set up Continous Integration (CI) GitHub triggers
* Fork this GitHub repo to your personal account
* Visit https://console.cloud.google.com/cloud-build/triggers
* Connect your GitHub repo
* Skip the "Create a push trigger (optional)" for now
* Edit ./setup_github_trigger.sh with your repo name
* Now, when you run ./setup_github_trigger.sh from the containers folder in CloudShell or Jupyter terminal, a trigger will be set up
* The trigger will rebuild Docker image any time a file in that container folder is committed

To Verify CI
* In AI Platform Notebooks, clone your personal GitHub repo
* cd to this directory
* Create Docker containers:  ./build_all.sh
* Change containers/bqtocsv/transform.py in some way (maybe add a print statement)
* Do a git commit
* Visit https://console.cloud.google.com/cloud-build/triggers and verify that the corresponding trigger is activated
* Verify that a new Docker image has been built and pushed to gcr.io

### 3b Verify CD
* Change containers/pipeline/mlp_babyweight.py to reference your project instead of cloud-training-demos
* Verify that submitting the pipeline still works from AI Platform Notebooks
* From a Terminal in AI Platform Notebooks
  * cd containers/pipeline
  * Run ./1_deploy_cloudrun.sh  your_pipelines_host. This will finish and tell you the URL end point.
  * Alternately, visit https://console.cloud.google.com/run to find the URL end point
  * Run ./2_deploy_cloudfunctions.sh cloud_run_url
  * Copy a new file into the preprocessed folder, or try running ./try_cloudfunction.sh
  * Looking at the Cloud Function and Cloud Run logs
  * Visit the kfp UI to see the new Experiment Run that has been launched.
  




