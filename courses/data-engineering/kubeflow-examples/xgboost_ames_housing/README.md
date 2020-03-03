# Ames housing value prediction using XGBoost on Kubeflow

In this example we will demonstrate how to use Kubeflow with XGBoost using the [Kaggle Ames Housing Prices prediction](https://www.kaggle.com/c/house-prices-advanced-regression-techniques/). We will do a detailed
walk-through of how to implement, train and serve the model. You will be able to run the exact same workload on-prem and/or on any cloud provider. We will be using [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/) to show how the end-to-end workflow runs on [Google Cloud Platform](https://cloud.google.com/). 

# Pre-requisites

As a part of running this setup on Google Cloud Platform, make sure you have enabled the [Google
Kubernetes Engine](https://cloud.google.com/kubernetes-engine/). In addition to that you will need to install
[Docker](https://docs.docker.com/install/) and [gcloud](https://cloud.google.com/sdk/downloads). Note that this setup can run on-prem and on any cloud provider, but here we will demonstrate GCP cloud option. Finally, follow the [instructions](https://www.kubeflow.org/docs/started/getting-started-gke/) to create a GKE cluster. 

# Steps
 * [Kubeflow Setup](#kubeflow-setup)
 * [Data Preparation](#data-preparation)
 * [Dockerfile](#dockerfile)
 * [Model Training on GKE](#model-training-on-gke)
 * [Model Export](#model-export)
 * [Model Serving Locally](#model-serving-locally)
 * [Deploying Model to Kubernetes Cluster](#model-serving-on-gke)

## Kubeflow Setup
In this part you will setup Kubeflow on an existing Kubernetes cluster. Checkout the Kubeflow [getting started guide](https://www.kubeflow.org/docs/started/getting-started/). 

## Data Preparation
You can download the dataset from the [Kaggle competition](https://www.kaggle.com/c/house-prices-advanced-regression-techniques/data). In order to make it convenient we have uploaded the dataset on GCS

```
gs://kubeflow-examples-data/ames_dataset/
```

## Dockerfile
We have attached a Dockerfile with this repo which you can use to create a
docker image. We have also uploaded the image to gcr.io, which you can use to
directly download the image.

```
IMAGE_NAME=ames-housing
VERSION=latest
```

Use `gcloud` command to get the GCP project

```
PROJECT_ID=`gcloud config get-value project`
```

Let's create a docker image from our Dockerfile

```
docker build -t gcr.io/$PROJECT_ID/${IMAGE_NAME}:${VERSION} .
```

Once the above command is successful you should be able to see the docker
images on your local machine by running `docker images`. Next we will upload the image to
[Google Container Registry](https://cloud.google.com/container-registry/)

```
gcloud auth configure-docker
docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${VERSION}
```

A public copy is available at `gcr.io/kubeflow-examples/ames-housing:latest`.


## Model training on GKE
In this section we will run the above docker container on a [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/). There are two steps to perform the training

 * Create a GKE cluster
   
 * Create a Persistent Volume
   * Follow the instructions [here](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/). You will need to run the following `kubectl create` commands in order to get the `claim` attached to the `pod`.
 
     ```
     kubectl create -f py-volume.yaml
     kubectl create -f py-claim.yaml
     ```

 
 * Run docker container on GKE
   * Use the `kubectl` command to run the image on GKE
   
     ```
     kubectl create -f py-job.yaml
     ```
   
     Once the above command finishes you will have an XGBoost model available at Persistent Volume `/mnt/xgboost/housing.dat`.

## Model Export
The model is exported to the location `/tmp/ames/housing.dat`. We will use [Seldon Core](https://github.com/SeldonIO/seldon-core/) to serve the model asset. In order to make the model servable we have created `xgboost/seldon_serve` with the following assets

 * `HousingServe.py`
 * `housing.dat`
 * `requirements.txt`

## Model Serving Locally
We are going to use [seldon-core](https://github.com/SeldonIO/seldon-core/) to serve the model. [HoussingServe.py](seldon_serve/HousingServe.py) contains the code to serve the model. You can find seldon core model wrapping details [here](https://github.com/SeldonIO/seldon-core/blob/master/docs/wrappers/python.md). The seldon-core microservice image can be built by the following command.

```
cd seldon_serve && s2i build . seldonio/seldon-core-s2i-python2:0.4 gcr.io/${PROJECT_ID}/housingserve:latest --loglevel=3
```



Let's run the docker image locally.

```
docker run -p 5000:5000 gcr.io/${PROJECT_ID}/housingserve:latest
```

Now you are ready to send requests on `localhost:5000`

```
curl -H "Content-Type: application/x-www-form-urlencoded" -d 'json={"data":{"tensor":{"shape":[1,37],"values":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37]}}}' http://localhost:5000/predict
```

The response looks like this.
```
{
  "data": {
    "names": [
      "t:0", 
      "t:1"
    ], 
    "tensor": {
      "shape": [
        1, 
        2
      ], 
      "values": [
        97522.359375, 
        97522.359375
      ]
    }
  }
}
```

## Model serving on GKE
One of the amazing features of Kubernetes is that you can run it anywhere i.e., local, on-prem and cloud. We will show you how to run your code on Google Kubernetes Engine. First off, start a GKE cluster.

Deploy Seldon core to your GKE cluster by following the instructions in the Deploy Seldon Core section [here](https://github.com/kubeflow/examples/blob/fb2fb26f710f7c03996f08d81607f5ebf7d5af09/github_issue_summarization/serving_the_model.md#deploy-seldon-core). Once everything is successful you can verify it using `kubectl get pods -n ${NAMESPACE}`.

```
NAME                                      READY     STATUS    RESTARTS   AGE
ambassador-849fb9c8c5-5kx6l               2/2       Running   0          16m
ambassador-849fb9c8c5-pww4j               2/2       Running   0          16m
ambassador-849fb9c8c5-zn6gl               2/2       Running   0          16m
redis-75c969d887-fjqt8                    1/1       Running   0          30s
seldon-cluster-manager-6c78b7d6c9-6qhtg   1/1       Running   0          30s
spartakus-volunteer-66cc8ccd5b-9f8tw      1/1       Running   0          16m
tf-hub-0                                  1/1       Running   0          16m
tf-job-dashboard-7b57c549c8-bfpp8         1/1       Running   0          16m
tf-job-operator-594d8c7ddd-lqn8r          1/1       Running   0          16m
```

Second, we need to upload our previously built docker image to `gcr.io`. A public image is available at `gcr.io/kubeflow-examples/housingserve:latest`

```
gcloud auth configure-docker
docker push gcr.io/${PROJECT_ID}/housingserve:latest
```

Finally, we can deploy the XGBoost model
```
ks generate seldon-serve-simple-v1alpha2 xgboost-ames   \
                                --name=xgboost-ames   \
                                --image=gcr.io/${PROJECT_ID}/housingserve:latest   \
                                --namespace=${NAMESPACE}   \
                                --replicas=1
                                
ks apply ${KF_ENV} -c xgboost-ames
```

## Sample request and response
Seldon Core uses ambassador to route its requests. To send requests to the model, you can port-forward the ambassador container locally:

```
kubectl port-forward $(kubectl get pods -n ${NAMESPACE} -l service=ambassador -o jsonpath='{.items[0].metadata.name}') -n ${NAMESPACE} 8080:80

```

Now you are ready to send requests on `localhost:8080`

```
curl -H "Content-Type:application/json" \
  -d '{"data":{"tensor":{"shape":[1,37],"values":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37]}}}' \
  http://localhost:8080/seldon/xgboost-ames/api/v0.1/predictions
```

```
{
  "meta": {
    "puid": "8buc4oo78m67716m2vevvgtpap",
    "tags": {
    },
    "routing": {
    }
  },
  "data": {
    "names": ["t:0", "t:1"],
    "tensor": {
      "shape": [1, 2],
      "values": [97522.359375, 97522.359375]
  }
}
```
