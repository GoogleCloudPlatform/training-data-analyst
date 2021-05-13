# Kubeflow Katib Component Samples

These samples demonstrate how to create a Kubeflow Pipeline using
[Katib](https://github.com/kubeflow/katib).
The source code for the Katib Pipeline component can be found
[here](../../../components/kubeflow/katib-launcher).

Check the following examples:

- Run Pipeline from Jupyter Notebook using Katib Experiment with
  [random search algorithm and early stopping](early-stopping.ipynb).

- Compile compressed YAML definition of the Pipeline using Katib Experiment with
  [Kubeflow MPIJob and Horovod training container](mpi-job-horovod.py).
