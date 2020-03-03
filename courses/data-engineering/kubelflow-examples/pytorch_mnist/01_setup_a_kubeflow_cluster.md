# Setup Kubeflow

In this part, you will setup Kubeflow on Google Kubernetes Engine.

## Requirements

*   A GCP project with sufficient [GPU quota](https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#gpu_quota) 
to train the model with the desired GPU, e.g., K80, P100, V100...
*   `kubectl` CLI (command line interface) pointing to the kubernetes cluster
    *   Make sure that you can run `kubectl get nodes` from your terminal
        successfully
*   The ksonnet CLI, v0.9.2 or higher: [ks](https://ksonnet.io/#get-started)
    * In case you want to install a particular version of ksonnet, you can run
    
        ```commandline
        export KS_VER=ks_0.11.0_linux_amd64
        wget -O /tmp/$KS_VER.tar.gz https://github.com/ksonnet/ksonnet/releases/download/v0.11.0/$KS_VER.tar.gz
        mkdir -p ${HOME}/bin
        tar -xvf /tmp/$KS_VER.tar.gz -C ${HOME}/bin
        export PATH=$PATH:${HOME}/bin/$KS_VER
        ```
## Kubeflow setup

Refer to the [user
guide](https://www.kubeflow.org/docs/started/getting-started/) for
detailed instructions on how to setup Kubeflow on your kubernetes cluster.
Specifically, complete the following sections:

*    [Deploy
Kubeflow](https://www.kubeflow.org/docs/started/getting-started-gke/) on Google Kubernetes Engine
        *   [Zone(s)](https://cloud.google.com/compute/docs/gpus/#gpus-list) must have the GPU types you specify, e.g., us-central1-b for Nvidia V100
        *   If you run into
        [API rate limiting errors](https://github.com/ksonnet/ksonnet/blob/master/docs/troubleshooting.md#github-rate-limiting-errors),
        ensure you have a `${GITHUB_TOKEN}` environment variable set.
        *   If you run into
        [RBAC permissions issues](https://www.kubeflow.org/docs/guides/troubleshooting/#rbac-clusters)
        running `ks apply` commands, be sure you have created a `cluster-admin` ClusterRoleBinding for your username.
*    [Setup a persistent disk using Google Filestore](https://www.kubeflow.org/docs/guides/gke/cloud-filestore/)
        *   We need a shared persistent disk to store our trained model
        as containers' filesystems are ephemeral.
        *   For this example, provision a `10GB` cluster-wide shared NFS mount with the
        name `kubeflow-gcfs`.
        *   Enable the component in the Kubeflow cluster with
        ```commandline
        ks apply default -c google-cloud-filestore-pv
        ```
*    [Enable Seldon component to serve our Pytorch models](https://www.kubeflow.org/docs/guides/components/seldon/#serve-a-model-using-seldon)
        *   Install the seldon package, generate the core component as per the instructions
        *   Enable the component in the Kubeflow cluster with
        ```commandline
        ks apply default -c seldon
        ```
After completing that, you should have the following ready:

*   A ksonnet app in a directory named `ks_app`
*   An output similar to this for `kubectl get pods` command

```commandline
ambassador-7fb86f6bc5-8xj5h                      3/3       Running     0          13m
ambassador-7fb86f6bc5-h2hmt                      3/3       Running     0          13m
ambassador-7fb86f6bc5-tz98s                      3/3       Running     0          13m
argo-ui-7b6585d85d-mmxbb                         1/1       Running     0          13m
centraldashboard-f8d7d97fb-5g76z                 1/1       Running     0          13m
cert-manager-798d77c76-wflcb                     1/1       Running     0          12m
cloud-endpoints-controller-b55c586b6-7pdnn       1/1       Running     0          12m
cm-acme-http-solver-8lcvn                        1/1       Running     0          11m
envoy-79ff8d86b-4dgg7                            2/2       Running     2          12m
envoy-79ff8d86b-t6mv8                            2/2       Running     2          12m
envoy-79ff8d86b-xbfdj                            2/2       Running     2          12m
iap-enabler-6565b855d6-j2rt6                     1/1       Running     0          12m
ingress-bootstrap-kfzmg                          1/1       Running     0          12m
kube-metacontroller-6d567f9fb4-6g5sr             1/1       Running     0          12m
modeldb-backend-69dfc464df-h9lt7                 1/1       Running     0          12m
modeldb-db-6cf5bb764-qcxc7                       1/1       Running     0          12m
modeldb-frontend-795bcf6df9-8smn8                1/1       Running     0          12m
pytorch-operator-76f89745c-2qtt9                 1/1       Running     0          12m
seldon-redis-6cfc779655-lvphr                    1/1       Running     0          6m
seldon-seldon-cluster-manager-54c7794dcb-jdq6p   1/1       Running     0          6m
set-gcfs-permissions-w65j9                       0/1       Completed   0          18s
spartakus-volunteer-77446c94b5-7f5vf             1/1       Running     0          12m
studyjob-controller-68f5948984-c66g5             1/1       Running     0          12m
tf-hub-0                                         1/1       Running     0          13m
tf-job-dashboard-7cddcdf9c4-bqwbg                1/1       Running     0          13m
tf-job-operator-v1alpha2-6566f45db-v78tp         1/1       Running     0          13m
vizier-core-6d8c9d7bf7-chkkc                     1/1       Running     1          12m
vizier-db-cc59bc8bd-bgvp6                        1/1       Running     0          12m
vizier-suggestion-grid-76fb6b49c7-c22ss          1/1       Running     0          12m
vizier-suggestion-random-c5c64dfc9-svqc8         1/1       Running     0          12m
whoami-app-b7fb9f875-hchzc                       1/1       Running     0          12m
workflow-controller-59c7967f59-df424             1/1       Running     0          13m
```

*   A seldon component to serve our models
*   A Pytorch operator to train our models
*   A 10GB Filestore instance volume "kubeflow-gcfs"

## Summary

*   We deployed a Kubernetes cluster with [Deployment Manager using kfctl.sh script](https://www.kubeflow.org/docs/started/getting-started-gke/#understanding-the-deployment-process)
*   We created a ksonnet app for our Kubeflow deployment
*   We deployed the Kubeflow components to our kubernetes cluster
*   We created a persistent disk using Google Filestore for storing our trained model

*Next*: [Training the model](02_distributed_training.md)