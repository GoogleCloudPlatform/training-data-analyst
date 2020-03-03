# From Zero to Kubeflow

Video link: [YouTube](https://www.youtube.com/watch?v=AF-WH967_s4)

## Description

Michelle Casbon gives a straightforward walkthrough of two different ways to
install Kubeflow from scratch on GCP:

* Web-based - [Click-to-deploy](https://deploy.kubeflow.cloud)
* CLI - [kfctl](https://www.kubeflow.org/docs/gke/deploy/deploy-cli/)

## Commands

The following Terminal commands are used.

### Download the `kfctl` binary

```
export KUBEFLOW_TAG=0.5.1
wget -P /tmp https://github.com/kubeflow/kubeflow/releases/download/v${KUBEFLOW_TAG}/kfctl_v${KUBEFLOW_TAG}_darwin.tar.gz
tar -xvf /tmp/kfctl_v${KUBEFLOW_TAG}_darwin.tar.gz -C ${HOME}/bin
```

### Generate the project directory

```
export PROJECT_ID=<project_id>
export CLIENT_ID=<oauth_client_id>
export CLIENT_SECRET=<oauth_client_secret>
kfctl init kubeflow-cli --platform gcp --project ${PROJECT_ID}
```

### Generate all files

```
kfctl generate all --zone us-central1-c
```

### Create all platform and Kubernetes objects

```
kfctl apply all 
```

## Links

* [codelabs.developers.google.com](https://codelabs.developers.google.com/)
* [github.com/kubeflow/examples](https://github.com/kubeflow/examples)
* [kubeflow.org](https://www.kubeflow.org/)

