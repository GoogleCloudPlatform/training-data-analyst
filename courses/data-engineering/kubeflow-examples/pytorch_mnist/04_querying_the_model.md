# Querying the model

In this section, you will setup a web interface that can interact with a trained model server.


The web UI uses a Flask server to host the HTML/CSS/JavaScript files for the web page.
The Python program, mnist_client.py, contains a function that interacts directly with the prediction GRPC API exposed by our model server, 
where name `mnist-classifier` is the deployment name of our model server, address `ambassador` and port `80` point to the Ambassador endpoint, 
which will route the request to the Seldon model service.

The following steps describe how to deploy the docker image in your Kubeflow cluster, the `web-ui` directory also contains a Dockerfile to build the application into a container image.

## Prerequisites

Ensure that your model is live and listening for GRPC requests as described in
[serving](03_serving_the_model.md).

## Deploy the front-end docker image to your kubernetes cluster

The folder `ks_app` contains some pre-defined ksonnet components as we saw in step 3,
including a web-ui component which we will apply now.

```bash
cd ks_app
ks apply ${KF_ENV} -c web-ui
```

## View results from the frontend

In a browser, navigate to the Kubeflow URI `https://<name>.endpoints.<project>.cloud.goog/pytorch-ui/`, 
Ambassador routes requests to the prefix `/pytorch-ui/` to our deployed service `web-ui`



*Next*: [Teardown](05_teardown.md)

*Back*: [Serving the Model](03_serving_the_model.md)
