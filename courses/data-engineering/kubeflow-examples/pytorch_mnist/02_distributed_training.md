# Distributed training using Estimator

Requires Pytorch 0.4 or later.
Requires [StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/) capable of creating ReadWriteMany persistent volumes.

On GKE you can follow [GCFS documentation](https://master.kubeflow.org/docs/guides/gke/cloud-filestore/) to enable it.

In this distributed training example we will show how to train a model using [DDP](https://pytorch.org/docs/stable/nn.html#torch.nn.parallel.DistributedDataParallel) in
distributed MPI-backend with [Openmpi](https://www.open-mpi.org/). This example parallelizes the application of the given module by
splitting the input across the specified devices by chunking in the batch dimension. The module is replicated on each machine and each device, and
each such replica handles a portion of the input. During the backwards pass, gradients from each node are averaged.

### Strong vs Weak Scaling

This example implements a strong scaling for mnist, which means the global batchsize is fixed no matter how many nodes we use.
See more info about Strong vs Weak Scaling at [wiki](https://en.wikipedia.org/wiki/Scalability#Weak_versus_strong_scaling).  
Since this is a strong scaling example, we should perform an average after the all_reduce, which is the same as [torch.nn.parallel.DistributedDataParallel](https://github.com/pytorch/pytorch/blob/master/torch/nn/parallel/distributed.py#L338).

## How to run it

Deploy the PyTorchJob resource to start training the CPU & GPU models:

### If running on Kubeflow 0.4.x:
```bash
cd ks_app
ks env add ${KF_ENV}
ks apply ${KF_ENV} -c train_model_CPU_v1beta1
ks apply ${KF_ENV} -c train_model_GPU_v1beta1
```

### If running on Kubeflow 0.5.x or newer:
```bash
cd ks_app
ks env add ${KF_ENV}
ks apply ${KF_ENV} -c train_model_CPU_v1beta2
ks apply ${KF_ENV} -c train_model_GPU_v1beta2
```

## What just happened?

With the commands above we have created Custom Resource that has been defined and enabled during Kubeflow
installation, namely `PyTorchJob`.

If you look at [job_mnist_DDP_GPU.yaml](https://github.com/kubeflow/examples/blob/master/pytorch_mnist/training/ddp/mnist/gpu/v1beta1/job_mnist_DDP_GPU.yaml) few things are worth mentioning.

1. We mount our shared persistent disk as /mnt/kubeflow-gcfs for our PyTorchJob, where models will be saved at the end of the epochs
2. Allocate one GPU to our container
2. Run our PyTorchJob

## Understanding PyTorchJob

Each PyTorchJob will run 2 types of Pods.

Master should always have 1 replica. This is main worker which will show us status of overall job and aggregate all the model parameters.

Worker is Pod which will run training. It can have any number of replicas.
Refer to [Pod definition](https://kubernetes.io/docs/concepts/workloads/pods/pod/) documentation for details.

## Understanding training code

There are few things required for this approach to work.

First we need to install openmpi in each worker

1. If node is Master, rank=0 - Aggregate all parameters and save model to disk after all epochs complete
2. If node is Worker - run feature preparation and parse input dataset for the particular data split/partition

Finally we use `torch.nn.parallel.DistributedDataParallel` function to enable distributed training on this model.

## Input function

This example parallelizes by splitting the input across the specified devices by chunking in the batch dimension.
For that reason we need to prepare a function that will slice input data to batches, which are then run on each worker.
Pytorch offers different ways to implement that, in this particular example we are using `torch.utils.data.distributed.DistributedSampler(dataset)` 
to partition a dataset into different chuncks.

## Model

After training is complete, our model can be found in "pytorch/model" PVC.

*Next*: [Serving the Model](03_serving_the_model.md)

*Back*: [Setup](01_setup_a_kubeflow_cluster.md)
