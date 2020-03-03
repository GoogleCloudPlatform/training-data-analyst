Using Kubeflow for Financial Time Series
====================

In this example, we will walk through the exploration, training and serving of a machine learning model by leveraging Kubeflow's main components. 
We will use the [Machine Learning with Financial Time Series Data](https://cloud.google.com/solutions/machine-learning-with-financial-time-series-data) use case.

## Goals

There are two primary goals for this tutorial:

*   Demonstrate an End-to-End kubeflow example
*   Present a financial time series model example

By the end of this tutorial, you should learn how to:

*   Setup a Kubeflow cluster 
*   Spawn a Jupyter Notebook on the cluster
*   Train a time-series model using TensorFlow and GPUs on the cluster
*   Serve the model using [TF Serving](https://www.kubeflow.org/docs/components/serving/tfserving_new/)
*   Query the model via your local machine
*   Automate the steps 1/ preprocess, 2/ train and 3/ model deployment through a kubeflow pipeline

### Pre-requisites
You can use a Google Cloud Shell to follow the steps outlined below.
In that case you can skip the requirements below as these depencies are pre-installed.
You might also need to install ```uuid-runtime``` via ```sudo apt-get install uuid-runtime```.

Alternatively, you can work from your local environment.
In that case you will need a Linux or Mac environment with Python 3.6.x and install the [Cloud SDK](https://cloud.google.com/sdk/).

Independent of the machine that you are using, you will need access to a Google Cloud Project and its GKE resources.

### Deploying Kubeflow on GKE
Please follow the instructions on how to deploy Kubeflow to GKE on the 
[Deploy using CLI](https://www.kubeflow.org/docs/gke/deploy/deploy-cli/) page with the following exceptions:

- After the step `kfctl build -V -f ${CONFIG_URI}` make sure you add 
'https://www.googleapis.com/auth/cloud-platform' to the `VM_OAUTH_SCOPES` in the file `{KF_NAME}/gcp_config/cluster.ninja`. This will allow the machines to make use of the BigQuery API, which we need for our use case as the data is stored in BigQuery, and to store data on Google Cloud Storage. 
- After the step `kfctl build -V -f ${CONFIG_URI}` make sure you set `enableNodeAutoprovisioning` to false in  `{KF_NAME}/gcp_config/cluster-kubeflow.yaml` as we will work with our dedicated gpu-pool that Kubeflow deployment foresees. 
The [node autoprovisioning](https://cloud.google.com/kubernetes-engine/docs/how-to/node-auto-provisioning) can be useful to autoscale the cluster with non-user defined node pools.


### Cloning the Examples 

Clone the examples repository and change directory to the financial time series example:
```
git clone https://github.com/kubeflow/examples.git
cd examples/financial_time_series/
```

### Explore the Kubeflow UI
After some time (about 10-15 minutes), an endpoint should now be available at `https://<KF_NAME>.endpoints.<project_id>.cloud.goog/`.
From this page you can navigate between the different Kubeflow components.

### Exploration via Jupyter Hub
The [JupyterHub](https://github.com/jupyterhub/jupyterhub) component of Kubeflow allows us to spin up Jupyter Notebooks quite easily. 
In the notebook we will investigate the data and start building a feasible machine learning model for the specific problem.

From the Kubeflow starting page, you can click on the `Notebook Servers` tab.
Make sure you select a namespace on the top left and hit the 'new server' 
button. You can just fill in an appropiate name and leave all the options to 
the defaults. You can simply upload the [notebook](https://github.com/kubeflow/examples/blob/master/financial_time_series/Financial%20Time%20Series%20with%20Finance%20Data.ipynb) and walk through it step by step to better understand the problem and suggested solution(s).
In this example, the goal is not focus on the notebook itself but rather on how this notebook is being translated in more scalable training jobs and later on serving.

### Training at scale with TF-jobs
The next step is to 're-factor' the notebook code into Python scripts which can then be containerized onto a Docker image.
In the folder ```tensorflow-model``` you can find these scripts together with a ```Dockerfile```.
Subsequently we will build a docker image on Google Cloud by running following command:

```
cd tensorflow_model/
export TRAIN_PATH=gcr.io/<project>/<image-name>/cpu:v1
gcloud builds submit --tag $TRAIN_PATH .
```

We will create a bucket to store our data and model artifacts:

```
# create storage bucket that will be used to store models
BUCKET_NAME=<your-bucket-name>
gsutil mb gs://$BUCKET_NAME/
```

Now that we have an image ready on Google Cloud Container Registry, it's time we start launching a training job.
Please have a look at the tfjob resource in `CPU/tfjob1.yaml` and update the 
image and bucket reference. In this case we
 are using a very simple definition of a 
 [TF-job](https://www.kubeflow.org/docs/components/training/tftraining/), 
 it only has a single worker as we are not doing any advanced training set-up (e.g. distributed training).

Next we can launch the tf-job to our Kubeflow cluster and follow the progress via the logs of the pod.

```
kubectl apply -f CPU/tfjob1.yaml
POD_NAME=$(kubectl get pods -n kubeflow --selector=tf-job-name=tfjob-flat \
      --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
kubectl logs -f $POD_NAME -n kubeflow
```

In the logs you can see that the trained model is being exported to google cloud storage. This saved model will be used later on for serving requests. With these parameters, the accuracy on the test set is approximating about 60%. 


### Deploy and serve with TF-serving
Once the model is trained, the next step will be to deploy it and serve requests.
We will use the standard TF-serving module that Kubeflow offers.
Please have a look at the serving manifest `tfserving.yaml` and update the bucket name. 
We will use a ClusterIP to expose the service only inside the cluster. To 
reach out securely from outside of the cluster, you could use the secured 
set-up via the istio ingress-gateway, which 
Kubeflow offers out-of-the-box. For more information, see the
 [documentation](https://www.kubeflow.org/docs/components/serving/tfserving_new/).

```
kubectl apply -f tfserving.yaml
```

After running these commands, a deployment and service will be launched on Kubernetes that will enable you to easily send requests to get predictions from your module.
Let's check if the model is loaded successfully.

```
POD=`kubectl get pods -n kubeflow --selector=app=model | awk '{print $1}' | tail -1`
kubectl logs -f $POD -n kubeflow
```

We will do a local test via HTTP to illustrate how to get results from this serving component. Once the pod is up we can set up port-forwarding to our localhost.
```
kubectl port-forward $POD 8500:8500 -n kubeflow 2>&1 >/dev/null &
```

Now the only thing we need to do is send a request to ```localhost:8500``` with the expected input of the saved model and it will return a prediction.
The saved model expects a time series from closing stocks and spits out the prediction as a 0 (S&P closes positive) or 1 (S&P closes negative) together with the version of the saved model which was memorized upon saving the model.
Let's start with a script that populates a request with random numbers to test the service.

```
pip3 install numpy requests
python3 -m serving_requests.request_random
```

The output should return an integer, 0 or 1 as explained above, and a string that represents the tag of the model.
There is another script available that builds a more practical request, with time series data of closing stocks for a certain date.
In the following script, the same date is used as the one used at the end of the notebook ```Machine Learning with Financial Time Series Data.ipynb``` for comparison reasons.

```
pip3 install -r requirements.txt
python3 -m serving_requests.request
```

The response should indicate that S&P index is expected to close positive (0) but from the actual data (which is prospected in the notebook mentioned above) we can see that it actually closed negative that day.
Let's get back to training and see if we can improve our accuracy.

### Running another TF-job and serving update
Most likely a single training job will never be sufficient. It is very common to create a continuous training pipeline to iterate training and verify the output.
Please have a look at the serving manifest `CPU/tfjob2.yaml` and update the 
image and bucket reference. 
This time, we will train a more complex neural network with several hidden layers.


```
kubectl apply -f CPU/tfjob2.yaml
```

Verify the logs via:

```
POD_NAME=$(kubectl get pods -n kubeflow --selector=tf-job-name=tfjob-deep \
      --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
kubectl logs -f $POD_NAME -n kubeflow
```

You should notice that the training now takes a few minutes instead of less than one minute.
 The accuracy on the test set is now 72%.
Our training job uploads the trained model to the serving directory of our running TF-serving component.
Let's see if we get a response from the new version and if the new model gets it right this time.

```
python3 -m serving_requests.request
```

The response returns the model tag 'v2' and  predicts the correct output 1, which means the S&P index closes negative, hurray!

### Running TF-job on a GPU

Can we also run the TF-job on a GPU?
Imagine the training job does not just take a few minutes but rather hours or days.
In this case we can reduce the training time by using a GPU. The GKE deployment script for Kubeflow automatically adds a GPU-pool that can scale as needed so you don’t need to pay for a GPU when you don’t need it. 
Note that the Kubeflow deployment also installs the necessary Nvidia drivers for you so there is no need for you to worry about extra GPU device plugins.

We will need another image that installs ```tensorflow-gpu``` and has the necessary drivers.

```
cp GPU/Dockerfile ./Dockerfile
export TRAIN_PATH_GPU=gcr.io/<project-name>/<image-name>/gpu:v1
gcloud builds submit --tag $TRAIN_PATH_GPU .
```

Please have a look at the slightly altered training job manifest `GPU/tfjob3
.yaml` and update the image and bucket reference. 
Note that the container now has a nodeSelector to point to the GPU-pool.
Next we can deploy the tf-job to our GPU by simply running following command.

```
kubectl apply -f GPU/tfjob3.yaml
```

First the pod will be unschedulable as there are no gpu-pool nodes available. This demand will be recognized by the kubernetes cluster and a node will be created on the gpu-pool automatically.
Once the pod is up, you can check the logs and verify that the training time is reduced compared to the previous tf-job.

```
POD_NAME=$(kubectl get pods -n kubeflow --selector=tf-job-name=tfjob-deep-gpu \
      --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
kubectl logs -f $POD_NAME -n kubeflow
```

### Kubeflow Pipelines
Up to now, we clustered the preprocessing, training and deploy in a single script to illustrate the TFJobs.
In practice, most often the preprocessing, training and deploy step will separated and they will need to run sequentially.
Kubeflow pipelines offers an easy way of chaining these steps together and we will illustrate that here.
As you can see, the script `run_preprocess_train_deploy.py` was using the scripts `run_preprocess.py`, `run_train.py` and `run_deploy.py` underlying.
The idea here is that these three steps will be containerized and chained together by Kubeflow pipelines.
We will also introduce a condition that we will only deploy the model if the accuracy on the test set surpasses a treshold of 70%.

Kubeflow Pipelines asks us to compile our pipeline Python3 file into a domain-specific-language. 
We do that with a tool called dsl-compile that comes with the Python3 SDK. So, first install that SDK:

```
pip3 install python-dateutil kfp==0.1.36
```

Please inspect the `ml_pipline.py` and update the `ml_pipeline.py` with the cpu image path that you built in the previous steps.
Then, compile the DSL, using:

```
python3 ml_pipeline.py
```

Now a file `ml_pipeline.py.tar_gz` is generated that we can upload to the kubeflow pipelines UI.
We will navigate again back to the Kubeflow UI homepage on `https://<KF_NAME>.endpoints.<project_id>.cloud.goog/` and click on the 'Pipelines' in the menu on the left side.


Once the page is open, click 'Upload pipeline' and select the tar.gz file.
If you click on the pipeline you can inspect the Directed Acyclic Graph (DAG).

![Pipeline Graph](./docs/img/pipeline_graph.png)

Next we can click on the pipeline and create a run. For each run you need to specify the params that you want to use. 
When the pipeline is running, you can inspect the logs:

![Pipeline UI](./docs/img/pipeline_logs.png)

This run with the less advanced model does not surpass the accuracy threshold and there is no deploy step.
Note that you can also see the accuracy metrics across the different runs from the Experiments page.
![Pipeline UI](./docs/img/run_metrics.png)

Also check that the more advanced model surpassed the accuracy threshold and was deployed by TF-serving.
![Pipeline UI](./docs/img/run_with_deploy.png)


### Clean up
To clean up, follow the instructions ['Delete using CLI'](https://www.kubeflow.org/docs/gke/deploy/delete-cli/) so that all components are 
deleted in a correct manner.
