# Serving the model

We are going to use [Seldon Core](https://github.com/SeldonIO/seldon-core) to serve the model. [IssueSummarization.py](notebooks/IssueSummarization.py) contains the code for this model. We will wrap this class into a seldon-core microservice which we can then deploy as a REST or GRPC API server.

> The model is written in Keras and when exported as a TensorFlow model seems to be incompatible with TensorFlow Serving. So we're using Seldon Core to serve this model since seldon-core allows you to serve any arbitrary model. More details [here](https://github.com/kubeflow/examples/issues/11#issuecomment-371005885).

#  Building a model server

You have two options for getting a model server

1. You can use the public model server image `gcr.io/kubeflow-examples/issue-summarization-model`

  * This server has a copy of the model and supporting assets baked into the container image
  * So you can just run this image to get a pre-trained model
  * Serving your own model using this server is discussed below

1. You can build your own model server as discussed below. For this you will need to install the [Source2Image executable s2i](https://github.com/openshift/source-to-image).


## Wrap the model into a Seldon Core microservice

Set a couple of environment variables to specify the GCP Project and the TAG you want to build the image for:

```
PROJECT=my-gcp-project
TAG=0.1
```

cd into the notebooks directory and run the following command (you will need [s2i](https://github.com/openshift/source-to-image) installed):

```
cd notebooks/
make build-model-image PROJECT=${PROJECT} TAG=${TAG}
```

This will use [S2I](https://github.com/openshift/source-to-image)  to wrap the inference code in `IssueSummarization.py` so it can be run and managed by Seldon Core.


Now you should see an image named `gcr.io/<gcr-repository-name>/issue-summarization:0.1` in your docker images. To test the model, you can run it locally using:

```
make start-docker-model-image PROJECT=${PROJECT} TAG=${TAG}
```

To send an example payload to the server run:

```
make test-model-image_local
```

or you can run a curl command explicitly such as:

```
curl -g http://localhost:5000/predict --data-urlencode 'json={"data":{"ndarray":[["try to stop flask from using multiple threads"]]}}'
```

To stop the running server run:

```
make stop-docker-model-image
```

You can push the image by running:

```
make push-model-image PROJECT=${PROJECT} TAG=${TAG}
```

> You can find more details about wrapping a model with seldon-core [here](https://github.com/SeldonIO/seldon-core/blob/master/docs/wrappers/python.md)


# Deploying the model to your kubernetes cluster

Now that we have an image with our model server, we can deploy it to our kubernetes cluster. We need to first deploy seldon-core to our cluster.

## Deploy Seldon Core


Install the CRD and its controller using the seldon prototype. If you used
`kfctl` to install Kubeflow, seldon is already included and you can run
the following commands (if not, follow the
[quick start](https://www.kubeflow.org/docs/started/getting-started/#kubeflow-quick-start)
instructions to generate the k8s manifests first):

```bash
cd ks_app
# Generate the seldon component and deploy it
ks generate seldon seldon --namespace=${NAMESPACE}
ks apply ${KF_ENV} -c seldon
```

Seldon Core should now be running on your cluster. You can verify it by running
`kubectl get pods -n${NAMESPACE}`. You should see two pods named
`seldon-seldon-cluster-manager-*` and `seldon-redis-*`.

## Deploying the actual model

Now that you have seldon core deployed, you can deploy the model using the
`seldon-serve-simple-v1alpha2` prototype.

```bash
ks generate seldon-serve-simple-v1alpha2 issue-summarization-model \
  --name=issue-summarization \
  --image=gcr.io/${PROJECT}/issue-summarization-model:${TAG} \
  --replicas=2
ks apply ${KF_ENV} -c issue-summarization-model
```

The model can take quite some time to become ready due to the loading times of the models and may be restarted if it fails the default liveness probe. If this happens you can add a custom livenessProbe to the issue-summarization.jsonnet file. Add the below to the container section:

```
   "livenessProbe": {
      "failureThreshold": 3,
      "initialDelaySeconds": 30,
      "periodSeconds": 5,
      "successThreshold": 1,
         "handler" : {
	    "tcpSocket": {
               "port": "http"
             }
      },
```

# Sample request and response

Seldon Core uses ambassador to route its requests. To send requests to the model, you can port-forward the ambassador container locally:

```
kubectl port-forward svc/ambassador -n ${NAMESPACE} 8080:80
```


```
curl -X POST -H 'Content-Type: application/json' -d '{"data":{"ndarray":[["issue overview add a new property to disable detection of image stream files those ended with -is.yml from target directory. expected behaviour by default cube should not process image stream files if user does not set it. current behaviour cube always try to execute -is.yml files which can cause some problems in most of cases, for example if you are using kuberentes instead of openshift or if you use together fabric8 maven plugin with cube"]]}}' http://localhost:8080/seldon/issue-summarization/api/v0.1/predictions
```

Response

```
{
  "meta": {
    "puid": "2rqt023g11gt7vfr0jnfkf1hsa",
    "tags": {
    },
    "routing": {
    }
  },
  "data": {
    "names": ["t:0"],
    "ndarray": [["add a new property"]]
  }
}
```

*Next*: [Querying the model](04_querying_the_model.md)

*Back*: [Training the model](02_training_the_model.md)
