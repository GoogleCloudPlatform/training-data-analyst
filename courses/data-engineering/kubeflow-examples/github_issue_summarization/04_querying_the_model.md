# Querying the model

In this section, you will setup a barebones web server that displays the
prediction provided by the previously deployed model.

The following steps describe how to build a docker image and deploy it locally,
where it accepts as input any arbitrary text and displays a machine-generated
summary.


## Prerequisites

Ensure that your model is live and listening for HTTP requests as described in
[serving](03_serving_the_model.md).


## Build the front-end docker image

To build the front-end docker image, issue the following commands:

```bash
cd docker
docker build -t gcr.io/gcr-repository-name/issue-summarization-ui:0.1 .
```

## Store the front-end docker image

To store the docker image in a location accessible to GKE, push it to the
container registry of your choice. Here, it is pushed to Google Container
Registry.

```bash
gcloud docker -- push gcr.io/gcr-repository-name/issue-summarization-ui:0.1
```

## Deploy the front-end docker image to your Kubernetes cluster

The folder [`ks_app`](ks_app) contains a ksonnet app. The
[ui component](ks_app/components/ui.jsonnet)
in `ks_app` contains the frontend deployment.

To avoid rate-limiting by the GitHub API, you will need an [authentication token](https://github.com/ksonnet/ksonnet/blob/master/docs/troubleshooting.md) stored in the form of an environment variable `${GITHUB_TOKEN}`. The token does not require any permissions and is only used to prevent anonymous API calls.

To use this token, set it as a parameter in the ui component:

```bash
cd ks_app
ks param set ui github_token ${GITHUB_TOKEN} --env ${KF_ENV}
```

To set the URL of your trained model, add it as a parameter:

```bash
ks param set ui modelUrl "http://issue-summarization.${NAMESPACE}.svc.cluster.local:8000/api/v0.1/predictions" --env ${KF_ENV}
```

To serve the frontend interface, apply the `ui` component of the ksonnet app:

```
ks apply ${KF_ENV} -c ui
```

## View results from the frontend

We use `ambassador` to route requests to the frontend. You can port-forward the
ambassador container locally:

```bash
kubectl port-forward svc/ambassador -n ${NAMESPACE} 8080:80
```

In a browser, navigate to `http://localhost:8080/issue-summarization/`, where
you will be greeted by a basic website. Press the *Populate Random Issue*
button, then click *Generate Title* to view 
a summary that was provided by your trained model.

*Next*: [Teardown](05_teardown.md)

*Back*: [Serving the Model](03_serving_the_model.md)
