# Arena demo

There are a series of examples about how to build deeplearning models with [Arena](https://github.com/kubeflow/arena). These demos will show how to run a pipeline standalone Job, MPI Job, TFJob(PS mode) and TensorFlow Estimator Job.

## Setup

1. Install the arena

```
kubectl create -f https://raw.githubusercontent.com/kubeflow/pipelines/eb830cd73ca148e5a1a6485a9374c2dc068314bc/samples/arena-samples/arena.yaml
```

2. Add addtional RBAC role to service account `pipeline-runner`

```
kubectl create -f https://raw.githubusercontent.com/kubeflow/pipelines/eb830cd73ca148e5a1a6485a9374c2dc068314bc/samples/arena-samples/arena_launcher_rbac.yaml
```

## Demos

- [Standalone Job](standalonejob/README.md)
- [MPI Job](mpi/README.md)
- [TensorFlow Estimator Job]()
- [TFJob]()

