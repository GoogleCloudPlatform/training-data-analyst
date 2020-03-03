# Kubeflow demo - Yelp restaurant reviews

This repository contains a demonstration of Kubeflow capabilities, suitable for
presentation to public audiences.

The base demo includes the following steps:

1. [Setup your environment](#1-setup-your-environment)
1. [Run training on CPUs](#2-run-training-on-cpus)
1. [Run training on TPUs](#3-run-training-on-tpus)
1. [Create the serving and UI components](#4-create-the-serving-and-ui-components)
1. [Bring up a notebook](#5-bring-up-a-notebook)
1. [Run a simple pipeline](#6-run-a-simple-pipeline)
1. [Perform hyperparameter tuning](#7-perform-hyperparameter-tuning)
1. [Run a better pipeline](#8-run-a-better-pipeline)
1. [Cleanup](#9-cleanup)

## 1. Setup your environment

Follow the instructions in
[demo_setup/README.md](https://github.com/kubeflow/examples/blob/master/demos/yelp_demo/demo_setup/README.md)
to setup your environment and install Kubeflow with pipelines on an
auto-provisioning GKE cluster with support for GPUs and TPUs.
_Note: This was tested using the_
_[v0.3.4-rc.1](https://github.com/kubeflow/kubeflow/tree/v0.3.4-rc.1)_
_branch with a cherry-pick of_
_[#1955](https://github.com/kubeflow/kubeflow/pull/1955)._

View the installed components in the GCP Console.
*  In the
[Kubernetes Engine](https://console.cloud.google.com/kubernetes)
section, you will see a new cluster ${CLUSTER} with 3 `n1-standard-1` nodes
*  Under
[Workloads](https://console.cloud.google.com/kubernetes/workload),
you will see all the default Kubeflow and pipeline components.

Source the environment file and activate the conda environment for pipelines:

```
source kubeflow-demo-base.env
source activate kfp
```

## 2. Run training on CPUs

Navigate to the ksonnet app directory created by `kfctl` and retrieve the
following files for the t2tcpu & t2ttpu jobs:

```
cd ks_app
cp ${DEMO_REPO}/demo/components/t2t*pu.* components
cp ${DEMO_REPO}/demo/components/params.* components
```

Set parameter values for training:

```
ks param set t2tcpu outputGCSPath ${GCS_TRAINING_OUTPUT_DIR_CPU}
```

Generate manifests and apply to cluster:

```
ks apply default -c t2tcpu
```

View the new training pod and wait until it has a `Running` status:

```
kubectl get pod -l tf_job_name=t2tcpu
```

View the logs to watch training commence:

```
kubectl logs -f t2tcpu-master-0 | grep INFO:tensorflow
```

## 3. Run training on TPUs

Set parameter values for training:

```
ks param set t2ttpu outputGCSPath ${GCS_TRAINING_OUTPUT_DIR_TPU}
```

Kick off training:

```
ks apply default -c t2ttpu
```

Verify that a TPU is being provisioned by viewing pod status. It should remain
in Pending state for 3-4 minutes with the message
`Creating Cloud TPUs for pod default/t2ttpu-master-0`.

```
kubectl describe pod t2ttpu-master-0
```

Once it has `Running` status, view the logs to watch training commence:

```
kubectl logs -f t2ttpu-master-0 | grep INFO:tensorflow
```

## 4. Create the serving and UI components

Retrieve the following files for the serving & UI components:

```
cp ${DEMO_REPO}/demo/components/serving.* components
cp ${DEMO_REPO}/demo/components/ui.* components
```

Create the serving and UI components:

```
ks apply default -c serving -c ui
```

Connect to the UI by forwarding a port to the ambassador service:

```
kubectl port-forward svc/ambassador 8080:80
```

Optional: If necessary, setup an SSH tunnel from your local laptop into the
compute instance connecting to GKE:

```
ssh ${HOST} -L 8080:localhost:8080
```

To show the naive version, navigate to
[localhost:8080/kubeflow_demo/](localhost:8080/kubeflow_demo/) from a browser.

To show the ML version, navigate to
[localhost:8080/kubeflow_demo/kubeflow](localhost:8080/kubeflow_demo/kubeflow) from a browser.

## 5. Bring up a notebook

Open a browser and connect to the Central Dashboard at [localhost:8080/](localhost:8080/).
Show the TF-job dashboard, then click on Jupyterhub.
Log in with any username and password combination and wait until the page
refreshes. Spawn a new pod with these resource requirements:

| Resource              | Value                                                                |
| --------------------- | -------------------------------------------------------------------- |
| Image                 | `gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-gpu:v0.2.1` |
| CPU                   | 2                                                                    |
| Memory                | 48G                                                                  |
| Extra Resource Limits | `{"nvidia.com/gpu":2}`                                               |

It will take a while for the pod to spawn. While you're waiting, watch for
autoprovisioning to occur. View the Workload and Node status in the GCP console.

Once the notebook environment is
available, open a new terminal and upload this
[Yelp notebook](notebooks/yelp.ipynb).

Ensure the kernel is set to Python 2, then execute the notebook.

## 6. Run a simple pipeline

Show the file `gpu-example-pipeline.py` as an example of a simple pipeline.

Compile it to create a .tar.gz file:

```
./gpu-example-pipeline.py
```

View the pipelines UI locally by forwarding a port to the ml-pipeline-ui pod:

```
kubectl port-forward svc/ml-pipeline-ui 8081:80
```

In the browser, navigate to `localhost:8081` and create a new pipeline by
uploading `gpu-example-pipeline.py.tar.gz`. Select the pipeline and click
_Create experiment_. Use all suggested defaults.

View the effects of autoprovisioning by observing the number of nodes increase.

Select _Experiments_ from the left-hand side, then _Runs_. Click on the
experiment run to view the graph and watch it execute.

View the container logs for the training step and take note of the low accuracy (~0.113).

## 7. Perform hyperparameter tuning

In order to determine parameters that result in higher accuracy, use Katib
to execute a Study, which defines a search space for performing training with a
range of different parameters.

Create a Study by applying an
[example file](https://github.com/kubeflow/katib/blob/master/examples/gpu-example.yaml)
to the cluster:

```
kubectl apply -f https://raw.githubusercontent.com/kubeflow/katib/master/examples/gpu-example.yaml
```

This creates a Studyjob object. To view it:

```
kubectl get studyjob
kubectl describe studyjobs gpu-example
```

To view the Katib UI, connect to the modeldb-frontend pod:

```
kubectl port-forward svc/katib-ui 8082:80
```

In the browser, navigate to `localhost:8082/katib` and click on the
gpu-example project. In the _Explore Visualizations_ section, select
_Optimizer_ in the _Group By_ dropdown, then click _Compare_.


View the creation of a new GPU node pool:

```
gcloud container node-pools list --cluster ${CLUSTER}
```

View the creation of new nodes:

```
kubectl get nodes
```

In the Katib UI, interact with the various graphs to determine which
combination of parameters results in the highest accuracy. Grouping by optimizer
type is one way to find consistently higher accuracies. Gather a set of
parameters to use in a new run of the pipeline.

## 8. Run a better pipeline

In the pipelines UI, clone the previous experiment run and update the arguments
to match the parameters for one of the runs with higher accuracies from the
Katib UI. Execute the pipeline and watch for the resulting accuracy, which
should be closer to 0.98.

Approximately 5 minutes after the last run completes, check the cluster nodes
to verify that GPU nodes have disappeared.


## 9. Cleanup

From the application directory created by `kfctl`, issue a cleanup command:

```
kfctl delete k8s
```

The cluster will scale back down to the default node pool, removing all nodes
created by NAP.

