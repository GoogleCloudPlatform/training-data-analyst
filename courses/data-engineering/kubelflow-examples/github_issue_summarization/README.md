# End-to-End kubeflow tutorial using a Sequence-to-Sequence model

This example demonstrates how you can use `kubeflow` end-to-end to train and
serve a Sequence-to-Sequence model on an existing kubernetes cluster. This
tutorial is based upon @hamelsmu's article ["How To Create Data Products That
Are Magical Using Sequence-to-Sequence
Models"](https://medium.com/@hamelhusain/how-to-create-data-products-that-are-magical-using-sequence-to-sequence-models-703f86a231f8).

## Goals

There are two primary goals for this tutorial:

*   Demonstrate an End-to-End kubeflow example
*   Present an End-to-End Sequence-to-Sequence model

By the end of this tutorial, you should learn how to:

*   Setup a Kubeflow cluster on an existing Kubernetes deployment
*   Spawn a Jupyter Notebook on the cluster
*   Spawn a shared-persistent storage across the cluster to store large
    datasets
*   Train a Sequence-to-Sequence model using TensorFlow and GPUs on the cluster
*   Serve the model using [Seldon Core](https://github.com/SeldonIO/seldon-core/)
*   Query the model from a simple front-end application

## Steps:

1.  [Setup a Kubeflow cluster](01_setup_a_kubeflow_cluster.md)
1.  Training the model. You can train the model using any of the following
    methods using Jupyter Notebook or using TFJob:
    -  [Training the model using a Jupyter Notebook](02_training_the_model.md)
    -  [Training the model using TFJob](02_training_the_model_tfjob.md)
    -  [Distributed Training using estimator and TFJob](02_distributed_training.md)
1.  [Serving the model](03_serving_the_model.md)
1.  [Querying the model](04_querying_the_model.md)
1.  [Teardown](05_teardown.md)
