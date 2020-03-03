# Serving the model

We are going to use [seldon-core](https://github.com/SeldonIO/seldon-core) to serve the model. [mnistddpserving.py](serving/seldon-wrapper/mnistddpserving.py) contains the code for this model. We will wrap this class into a seldon-core microservice 
which we can then deploy as a REST or GRPC API server.

> We are using seldon-core to serve this model since seldon-core allows you to serve any arbitrary model, including PyTorch.

##  Building a model server

We use the public model server image `gcr.io/kubeflow-examples/pytorch-mnist/serving`

  * This server loads the model from the mount point /mnt/kubeflow-gcfs and includes the supporting assets baked into the container image
  * So you can just run this image to get a pre-trained model from the shared persistent disk
  * Serving your own model using this server, exposing predict service as GRPC API

## Deploying the model to your Kubeflow cluster

As we have seldon core deployed from step 01, you can deploy the model once trained using the pre-defined ksonnet component, 
we need to setup our own environment `${KF_ENV}`, e.g., 'default'.

```bash
cd ks_app
ks env add ${KF_ENV}
ks apply ${KF_ENV} -c serving_model
```

## Testing model server

Seldon Core uses ambassador to route it's requests. To send requests to the model, you can port-forward the ambassador container locally:

```
kubectl port-forward $(kubectl get pods -n ${NAMESPACE} -l service=ambassador -o jsonpath='{.items[0].metadata.name}') -n ${NAMESPACE} 8080:80
```

And send a request that we know is not a torch MNIST image, which will return an error 500

```
curl -X POST -H 'Content-Type: application/json' -d '{"data":{"int":"8"}}' http://localhost:8080/seldon/mnist-classifier/api/v0.1/predictions
```

We should receive an error response as the model server is expecting a 1x786 vector representing a torch image, this will be sufficient to confirm the server model is up and running
(This is to avoid having to send manually a vector of 786 pixels, we will interact properly with the model using a web interface in the next session)

```
{
"timestamp":1540899355053,
"status":500,"error":"Internal Server Error",
"exception":"io.grpc.StatusRuntimeException",
"message":"UNKNOWN: Exception calling application: tensor is not a torch image.",
"path":"/api/v0.1/predictions"
}
```

## Information about how the Seldon wrapper works

In the serving/seldon-wrapper directory there is build_image.sh script that calls the docker Seldon wrapper to build our server image, 
exposing the predict service as GRPC API. 
You can invoke the same process with the below command in case you want to build your own image
```
docker run -v $(pwd):/my_model seldonio/core-python-wrapper:0.7 /my_model mnistddpserving 0.1 gcr.io --image-name=gcr-repository-name/name --grpc
```

You can then push the image by running `gcloud docker -- push gcr.io/gcr-repository-name/name:0.1` 
and modify the SeldonDeployment manifest to use your own image.

> You can find more details about wrapping a model with seldon-core [here](https://github.com/SeldonIO/seldon-core/blob/master/docs/wrappers/python.md)


*Next*: [Querying the model](04_querying_the_model.md)

*Back*: [Training the model](02_distributed_training.md)
