# Setup Kubeflow

In this section, you will setup Kubeflow on an existing Kubernetes cluster.

## Requirements

*   A Kubernetes cluster
    * To create a cluster, follow the instructions on the
      [Set up Kubernetes](https://www.kubeflow.org/docs/started/getting-started/#set-up-kubernetes)
      section of the Kubeflow Getting Started guide. We recommend using a
      managed service such as Google Kubernetes Engine (GKE).
      [This link](https://www.kubeflow.org/docs/started/getting-started-gke/)
      guides you through the process of using either
      [Click-to-Deploy](https://deploy.kubeflow.cloud/#/deploy) (a web-based UI) or
      [`kfctl`](https://github.com/kubeflow/kubeflow/blob/master/scripts/kfctl.sh)
      (a CLI tool) to generate a GKE cluster with all Kubeflow components
      installed. Note that there is no need to complete the Deploy Kubeflow steps
      below if you use either of these two tools.
*   The Kubernetes CLI `kubectl` pointing to the kubernetes cluster
    *   Make sure that you can run `kubectl get nodes` from your terminal
        successfully
*   The ksonnet CLI [`ks`](https://ksonnet.io/#get-started), v0.9.2 or higher:
    * In case you want to install a particular version of ksonnet, you can run
    
        ```bash
        export KS_VER=0.13.1
        export KS_BIN=ks_${KS_VER}_linux_amd64
        wget -O /tmp/${KS_BIN}.tar.gz https://github.com/ksonnet/ksonnet/releases/download/v${KS_VER}/${KS_BIN}.tar.gz
        mkdir -p ${HOME}/bin
        tar -xvf /tmp/${KS_BIN}.tar.gz -C ${HOME}/bin
        export PATH=$PATH:${HOME}/bin/${KS_BIN}
        ```

## Kubeflow setup

Refer to the [guide](https://www.kubeflow.org/docs/started/getting-started/) for
detailed instructions on how to setup Kubeflow on your Kubernetes cluster.
Specifically, complete the following sections:


* [Deploy Kubeflow](https://www.kubeflow.org/docs/other-guides/advanced/)
    * The latest version that was tested with this walkthrough was v0.4.0-rc.2.
    * The [`kfctl`](https://github.com/kubeflow/kubeflow/blob/master/scripts/kfctl.sh)
      CLI tool can be used to install Kubeflow on an existing cluster. Follow
      [this guide](https://www.kubeflow.org/docs/started/getting-started/#kubeflow-quick-start)
      to use `kfctl` to generate a ksonnet app, create Kubeflow manifests, and
      install all default components onto an existing Kubernetes cluster. Note
      that you can likely skip this step if you used
      [Click-to-Deploy](https://deploy.kubeflow.cloud/#/deploy)
      or `kfctl` to generate your cluster.

* [Setup a persistent disk](https://www.kubeflow.org/docs/guides/advanced/)

    * We need a shared persistent disk to store our training data since
      containers' filesystems are ephemeral and don't have a lot of storage space.

    * For this example, provision a `10GB` cluster-wide shared NFS mount with the
      name `github-issues-data`.

    * After the NFS is ready, delete the `jupyter-0` pod so that it gets recreated and
      picks up the NFS mount. You can delete it by running `kubectl delete pod
      jupyter-0 -n=${NAMESPACE}`

* [Bringing up a
Notebook](https://www.kubeflow.org/docs/guides/components/jupyter/)

    * When choosing an image for your cluster in the JupyterHub UI, use the
      image from this example:
      [`gcr.io/kubeflow-dev/issue-summarization-notebook-cpu:latest`](https://github.com/kubeflow/examples/blob/master/github_issue_summarization/workflow/Dockerfile).


After completing that, you should have the following ready:

* A ksonnet app in a directory named `ks_app`
* An output similar to this for `kubectl -n kubeflow get pods` command

```bash
NAME                                                      READY     STATUS         RESTARTS   AGE
ambassador-5cf8cd97d5-6qlpz                               1/1       Running        0          3m
ambassador-5cf8cd97d5-rqzkx                               1/1       Running        0          3m
ambassador-5cf8cd97d5-wz9hl                               1/1       Running        0          3m
argo-ui-7c9c69d464-xpphz                                  1/1       Running        0          3m
centraldashboard-6f47d694bd-7jfmw                         1/1       Running        0          3m
cert-manager-5cb7b9fb67-qjd9p                             1/1       Running        0          3m
cm-acme-http-solver-2jr47                                 1/1       Running        0          3m
ingress-bootstrap-x6whr                                   1/1       Running        0          3m
jupyter-0                                                 1/1       Running        0          3m
jupyter-chasm                                             1/1       Running        0          49s
katib-ui-54b4667bc6-cg4jk                                 1/1       Running        0          3m
metacontroller-0                                          1/1       Running        0          3m
minio-7bfcc6c7b9-qrshc                                    1/1       Running        0          3m
ml-pipeline-b59b58dd6-bwm8t                               1/1       Running        0          3m
ml-pipeline-persistenceagent-9ff99498c-v4k8f              1/1       Running        0          3m
ml-pipeline-scheduledworkflow-78794fd86f-4tzxp            1/1       Running        0          3m
ml-pipeline-ui-9884fd997-7jkdk                            1/1       Running        0          3m
ml-pipelines-load-samples-668gj                           0/1       Completed      0          3m
mysql-6f6b5f7b64-qgbkz                                    1/1       Running        0          3m
pytorch-operator-6f87db67b7-nld5h                         1/1       Running        0          3m
spartakus-volunteer-7c77dc796-7jgtd                       1/1       Running        0          3m
studyjob-controller-68c6fc5bc8-jkc9q                      1/1       Running        0          3m
tf-job-dashboard-5f986cf99d-kb6gp                         1/1       Running        0          3m
tf-job-operator-v1beta1-5876c48976-q96nh                  1/1       Running        0          3m
vizier-core-78f57695d6-5t8z7                              1/1       Running        0          3m
vizier-core-rest-7d7dd7dbb8-dbr7n                         1/1       Running        0          3m
vizier-db-777675b958-c46qh                                1/1       Running        0          3m
vizier-suggestion-bayesianoptimization-7f46d8cb47-wlltt   1/1       Running        0          3m
vizier-suggestion-grid-64c5f8bdf-2bznv                    1/1       Running        0          3m
vizier-suggestion-hyperband-8546bf5885-54hr6              1/1       Running        0          3m
vizier-suggestion-random-c4c8d8667-l96vs                  1/1       Running        0          3m
whoami-app-7b575b555d-85nb8                               1/1       Running        0          3m
workflow-controller-5c95f95f58-hprd5                      1/1       Running        0          3m
```

*   A Jupyter Notebook accessible at http://127.0.0.1:8000
*   A 10GB mount `/mnt/github-issues-data` in your Jupyter Notebook pod. Check this
    by running `!df` in your Jupyter Notebook.

## Summary

*   We created a ksonnet app for our kubeflow deployment: `ks_app`.
*   We deployed the default Kubeflow components to our Kubernetes cluster.
*   We created a disk for storing our training data.
*   We connected to JupyterHub and spawned a new Jupyter notebook.
*   For additional details and self-paced learning scenarios related to this
    example, see the
    [Resources](https://www.kubeflow.org/docs/started/getting-started/#resources)
    section of the
    [Getting Started Guide](https://www.kubeflow.org/docs/started/getting-started/).

*Next*: [Training the model with a notebook](02_training_the_model.md)
