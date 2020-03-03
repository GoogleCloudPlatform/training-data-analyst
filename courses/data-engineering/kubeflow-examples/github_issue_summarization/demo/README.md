# Demo

This folder contains the resources needed by the Kubeflow DevRel team
to setup a public demo of the GitHub Issue Summarization Example.

## Public gh-demo.kubeflow.org

We currently run a public instance of the ui at **gh-demo.kubeflow.org**

The current setup is as follows

```
PROJECT=kubecon-gh-demo-1
CLUSTER=gh-demo-1003
ZONE=us-east1-d
```

## Directory contents

* **gh-app** - This contains the ksonnet for deploying the public
  instance of the model and ui.
* **gh-demo-1003** - This is the app created by kfctl

## Setting up the demo

Here are the instructions for setting up the demo.

1. Follow the [GKE instructions](https://www.kubeflow.org/docs/started/getting-started-gke/) for deploying Kubeflow

	* If you are using PROJECT **kubecon-gh-demo-1** you can reuse the existing OAuth client
		* Use the Cloud console to lookup Client ID and secret and set the
		  corresponding environment variables

		* You will also need to add an authorized redirect URI for the new 
		   Kubeflow deployment

1. Follow the [instructions](https://www.kubeflow.org/docs/guides/gke/cloud-filestore/) to Setup an NFS share

   * This is needed to do distributed training with the TF estimator example

1. Create static IP for serving **gh-demo.kubeflow.org**

   ```
   gcloud --project=${PROJECT}  deployment-manager deployments create  --config=gh-demo-dm-config.yaml gh-public-ui
   ```
1. Update the Cloud DNS record **gh-demo.kubeflow.org** in project **kubeflow-dns** to use the new static ip.

1. Create a namespace for serving the UI and model

   ```
   kubectl create namespace gh-public
   ```

1. Deploy Seldon controller in the namespace that will serve the public model


   * This is a work around for [kubeflow/kubeflow#1712](https://github.com/kubeflow/kubeflow/issues/1712)

   ```
   cd gh-demo-1003/ks_app
   ks env add gh-public --namespace=gh-public
   ks generate seldon seldon
   ks apply gh-public -c seldon
   ```

1. Create a secret with a GitHub token

   * Follow [GitHub's instructions](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/) to create a token

   * Then run the following command to create the secret
   
     ```
     kubectl -n gh-public create secret generic github-token --from-literal=github-token=${GITHUB_TOKEN}
     ```

1. Deploy the public UI and model

   ```
   cd gh-app
   ks env add gh-public --namespace=gh-public
   ks apply gh-public
   ```

### Training and Deploying the model.

We use the ksonnet app in
[github/kubeflow/examples/github_issue_summarization/ks_app](https://github.com/kubeflow/examples/tree/master/github_issue_summarization/ks_app)

The current environment is

```
export ENV=gh-demo-1003
```

Set a bucket for the job output
```
DAY=$(date +%Y%m%d)
ks param set --env=${ENV} tfjob output_model_gcs_bucket kubecon-gh-demo
ks param set --env=${ENV} tfjob output_model_gcs_path gh-demo/${DAY}/output
```

Run the job

```
ks apply ${ENV} -c tfjob
```


#### Using TF Estimator with Keras

1. Copy the data to the GCFS mount by launching a notebook and then running the following commands

   ```
   !mkdir -p /mnt/kubeflow-gcfs/gh-demo/data
   !gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
   !gsutil cp gs://kubeflow-examples/github-issue-summarization-data/github-issues.zip /mnt/kubeflow-gcfs/gh-demo/data
   !unzip /mnt/kubeflow-gcfs/gh-demo/data/github-issues.zip
   !cp github_issues.csv /mnt/kubeflow-gcfs/gh-demo/data/
   ```

   * TODO(jlewi): Can we modify the existing job that downloads data to a PVC to do this?

1. Run the estimator job

   ```
   ks apply ${ENV} -c tfjob-estimator
   ```
1. Run TensorBoard

   ```
   ks apply ${ENV} -c tensorboard-pvc-tb
   ```
