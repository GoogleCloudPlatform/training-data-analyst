# Distributed training using Estimator

Distributed training with Keras currently does not work. Do not follow this guide
until these issues have been resolved:

* [kubeflow/examples#280](https://github.com/kubeflow/examples/issues/280)
* [kubeflow/examples#196](https://github.com/kubeflow/examples/issues/196)

Requires TensorFlow 1.9 or later.
Requires [StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/) capable of creating ReadWriteMany persistent volumes.

On GKE you can follow [GCFS documentation](https://master.kubeflow.org/docs/started/getting-started-gke/#using-gcfs-with-kubeflow) to enable it.

Estimator and Keras are both part of TensorFlow. These high-level APIs are designed
to make building models easier. In our distributed training example, we will show how both
APIs work together to help build models that will be trainable in both single node and
distributed manner.

## Keras and Estimators

Code required to run this example can be found in the
[distributed](https://github.com/kubeflow/examples/tree/master/github_issue_summarization/distributed)
directory.

You can read more about Estimators [here](https://www.tensorflow.org/guide/estimators).
In our example we will leverage `model_to_estimator` function that allows to turn existing tf.keras model to estimator, and therefore allow it to
seamlessly be trained distributed and integrate with `TF_CONFIG` variable which is generated as part of TFJob.

## How to run it

First, create PVC and download data. It would be good at this point to ensure that PVC use correct StorageClass etc.

```
kubectl create -f distributed/storage.yaml
```

Once download job finishes, you can run training by:

```
kubectl create -f distributed/tfjob.yaml
```

## Building image

To build image run:

```
docker build . -f distributed/Dockerfile
```

## What just happened?

With command above we have created Custom Resource that has been defined during Kubeflow
installation, namely `TFJob`.

If you look at [tfjob.yaml](https://github.com/kubeflow/examples/blob/master/github_issue_summarization/distributed/tfjob.yaml) few things are worth mentioning.

1. We create PVC for data and working directory for our TFJob where models will be saved at the end.
2. Next we run download [Job](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/) to download dataset and save it on one of PVCs
3. Run our TFJob

## Understanding TFJob

Each TFJob will run 3 types of Pods.

Master should always have 1 replica. This is main worker which will show us status of overall job.

PS, or Parameter server, is Pod that will hold all weights. It can have any number of replicas, recommended to have more than 1 - load will be spread between replicas, which would increase performance for io-bound training.

Worker is Pod which will run training. It can have any number of replicas.

Refer to [Pod definition](https://kubernetes.io/docs/concepts/workloads/pods/pod/) documentation for details.
TFJob differs slightly from regular Pod in a way that it will generate `TF_CONFIG` environmental variable in each Pod.
This variable is then consumed by Estimator and used to orchestrate distributed training.

## Understanding training code

There are few things required for this approach to work.

First we need to parse TF_CONFIG variable. This is required to run different logic per node role

1. If node is PS - run server.join()
2. If node is Master - run feature preparation and parse input dataset

After that we define Keras model. Please refer to [tf.keras documentation](https://www.tensorflow.org/guide/keras).

Finally we use `tf.keras.estimator.model_to_estimator` function to enable distributed training on this model.

## Input function

Estimators use [data parallelism](https://en.wikipedia.org/wiki/Data_parallelism) as it's default distribution model.
For that reason we need to prepare function that will slice input data to batches, which are then run on each worker.
Tensorflow provides several utility functions to help with that, and because we use numpy array as our input, `tf.estimator.inputs.numpy_input_fn` is perfect
tool for us. Please refer to [documentation](https://www.tensorflow.org/guide/premade_estimators#create_input_functions) for more information.

## Model

After training is complete, our model can be found in "model" PVC.

*Next*: [Serving the model](03_serving_the_model.md)

*Back*: [Setup a kubeflow cluster](01_setup_a_kubeflow_cluster.md)
