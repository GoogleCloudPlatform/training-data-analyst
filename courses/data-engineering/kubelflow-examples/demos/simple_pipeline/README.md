# Kubeflow demo - Simple pipeline

## Hyperparameter tuning and autoprovisioning GPU nodes

This folder contains a demonstration of Kubeflow capabilities, suitable for
presentation to public audiences.

This demo highlights the use of pipelines and hyperparameter tuning on a GKE
cluster with node autoprovisioning (NAP). A simple pipeline requests GPU resources, which triggers
node pool creation. This demo includes the following steps:

1. [Setup your environment](#1-setup-your-environment)
1. [Run a simple pipeline](#2-run-a-simple-pipeline)
1. [Perform hyperparameter tuning](#3-perform-hyperparameter-tuning)
1. [Run a better pipeline](#4-run-a-better-pipeline)

## 1. Setup your environment

Follow the instructions in
[demo_setup/README.md](https://github.com/kubeflow/examples/blob/master/demos/simple_pipeline/demo_setup/README.md)
to setup your environment and install Kubeflow with pipelines on an
autoprovisioning GKE cluster.

View the installed components in the GCP Console.
*  In the
[Kubernetes Engine](https://console.cloud.google.com/kubernetes)
section, you will see a new cluster ${CLUSTER} with 3 `n1-standard-1` nodes
*  Under
[Workloads](https://console.cloud.google.com/kubernetes/workload),
you will see all the default Kubeflow and pipeline components.

Source the environment file and activate the conda environment for pipelines:

```
source kubeflow-demo-simple-pipeline.env
source activate kfp
```

## 2. Run a simple pipeline

Show the file `gpu-example-pipeline.py` as an example of a simple pipeline.

Compile it to create a .tar.gz file:

```
./gpu-example-pipeline.py
```

View the pipelines UI locally by forwarding a port to the ml-pipeline-ui pod:

```
PIPELINES_POD=$(kubectl get po -l app=ml-pipeline-ui | \
  grep ml-pipeline-ui | \
  head -n 1 | \
  cut -d " " -f 1 )
kubectl port-forward ${PIPELINES_POD} 8080:3000
```

In the browser, navigate to `localhost:8080` and create a new pipeline by
uploading `gpu-example-pipeline.py.tar.gz`. Select the pipeline and click
_Create experiment_. Use all suggested defaults.

View the effects of autoprovisioning by observing the number of nodes increase.

Select _Experiments_ from the left-hand side, then _Runs_. Click on the
experiment run to view the graph and watch it execute.

View the container logs for the training step and take note of the low accuracy (~0.113).

## 3. Perform hyperparameter tuning

In order to determine parameters that result in higher accuracy, use Katib
to execute a Study, which defines a search space for performing training with a
range of different parameters.

Create a Study by applying an
[example file](https://github.com/kubeflow/examples/blob/master/demos/simple_pipeline/gpu-example-katib.yaml)
to the cluster:

```
kubectl apply -f gpu-example-katib.yaml
```

This creates a Studyjob object. To view it:

```
kubectl get studyjob
kubectl describe studyjobs gpu-example
```

To view the Katib UI, connect to the modeldb-frontend pod:

```
KATIB_POD=$(kubectl get po -l app=modeldb,component=frontend | \
  grep modeldb-frontend | \
  head -n 1 | \
  cut -d " " -f 1 )
kubectl port-forward ${KATIB_POD} 8081:3000
```

In the browser, navigate to `localhost:8081/katib` and click on the
gpu-example project. In the _Explore Visualizations_ section, select
_Optimizer_ in the _Group By_ dropdown, then click _Compare_.

While you're waiting, watch for autoprovisioning to occur. View the pods in Pending status.

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

## 4. Run a better pipeline

In the pipelines UI, clone the previous experiment run and update the arguments
to match the parameters for one of the runs with higher accuracies from the
Katib UI. Execute the pipeline and watch for the resulting accuracy, which
should be closer to 0.98.

Approximately 5 minutes after the last run completes, check the cluster nodes
to verify that GPU nodes have disappeared.

