# Kubeflow Pipeline Tutorial 
[`Kubeflow Pipelines`](https://github.com/kubeflow/pipelines) is a platform for building and deploying portable, 
scalable machine learning (ML) pipelines or workflows based on Docker containers. 
The `Kubeflow Pipelines` platform consists of:
- A user interface for managing and tracking experiments, jobs, and runs.
- An engine for scheduling multi-step ML workflows.
- An SDK for defining and manipulating pipelines and components.
- Notebooks for interacting with the system using the SDK.

A pipeline is a description of an ML workflow, including all of the components in the workflow and 
how they combine in the form of a graph. The pipeline includes the definition of the inputs (parameters) required to 
run the pipeline and the inputs and outputs of each component. A pipeline component is a self-contained set of user 
code, packaged as a Docker image, that performs one step in the pipeline. For example, a component can be responsible 
for steps such as data preprocessing, data transformation, and model training.

## Content Overview:
In this tutorial, we designed a series of notebooks to demonstrate how to interact with `Kubeflow Pipelines` through the
[Kubeflow Pipelines SDK](https://github.com/kubeflow/pipelines/tree/master/sdk/python/kfp). In particular
- [00 Kubeflow Cluster Setup](00_Kubeflow_Cluster_Setup.ipynb): this notebook helps you deploy a Kubeflow 
cluster through CLI. Note that it is also possible to deploy the Kubeflow cluster though 
[UI](https://www.kubeflow.org/docs/gke/deploy/deploy-ui/)

Then, notebooks 01-04 use one concrete use case, 
[MNIST classification](https://www.tensorflow.org/tutorials/quickstart/beginner), to demonstrate different ways of
authoring a pipeline component: 
- [01 Lightweight Python Components](01_Lightweight_Python_Components.ipynb): this notebook demonstrates how to build a 
component through defining a standalone python function and then calling `kfp.components.func_to_container_op(func)` to 
convert, which can be used in a pipeline.

- [02 Local Development with Docker Image Components](02_Local_Development_with_Docker_Image_Components.ipynb): this 
notebook guides you on creating a pipeline component with `kfp.components.ContainerOp` from an existing Docker image 
which should contain the program to perform the task required in a particular step of your ML workflow.

- [03 Reusable Components](03_Reusable_Components.ipynb): this notebook describes the manual way of writing a full 
component program (in any language) and a component definition for it. Below is a summary of the steps involved in 
creating and using a component.
    - Write the program that contains your component’s logic. The program must use files and command-line arguments 
    to pass data to and from the component.
    - Containerize the program.
    - Write a component specification in YAML format that describes the component for the Kubeflow Pipelines system.
    - Use the Kubeflow Pipelines SDK to load your component, use it in a pipeline and run that pipeline.

- [04 Reusable and Pre-build Components as Pipeline](04_Reusable_and_Pre-build_Components_as_Pipeline.ipynb): this 
notebook combines our built components, together with a pre-build GCP AI Platform components 
and a lightweight component to compose a pipeline with three steps.
    - Train an MNIST model and export it to Google Cloud Storage.
    - Deploy the exported TensorFlow model on AI Platform Prediction service.
    - Test the deployment by calling the endpoint with test data.

## Running the Tutorial Notebooks
Please note that the above configuration is required for notebook service running outside Kubeflow environment. 
And the examples demonstrated are fully tested on notebook service for the following three situations:
- Notebook running on your personal computer
- [Notebook on AI Platform, Google Cloud Platform](https://cloud.google.com/ai-platform-notebooks/)
- [Notebook running inside Kubeflow cluster](https://www.kubeflow.org/docs/components/jupyter/)
 
For notebook running inside Kubeflow cluster, for example JupyterHub will be deployed together with Kubeflow Pipeline, 
the environemt variables such as service account and default project should have been pre-configured while 
setting up the cluster.

## Contributors
- [Shixin Luo](https://github.com/luotigerlsx)
- [Kumar Saurabh](https://github.com/saurabh24292)