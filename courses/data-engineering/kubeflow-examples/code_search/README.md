# Code Search on Kubeflow

This demo implements End-to-End Code Search on Kubeflow.

# Warning: Running this example can be very expensive

This example uses large amounts of computation and cost several hundred dollars to run E2E on Cloud.


# Prerequisites

**NOTE**: If using the JupyterHub Spawner on a Kubeflow cluster, use the Docker image 
`gcr.io/kubeflow-images-public/kubeflow-codelab-notebook` which has baked all the pre-prequisites.

* `Kubeflow Latest`
  This notebook assumes a Kubeflow cluster is already deployed. See
  [Getting Started with Kubeflow](https://www.kubeflow.org/docs/started/getting-started/).

* `Python 2.7` (bundled with `pip`) 
  For this demo, we will use Python 2.7. This restriction is due to [Apache Beam](https://beam.apache.org/),
  which does not support Python 3 yet (See [BEAM-1251](https://issues.apache.org/jira/browse/BEAM-1251)).

* `Google Cloud SDK`
  This example will use tools from the [Google Cloud SDK](https://cloud.google.com/sdk/). The SDK 
  must be authenticated and authorized. See
  [Authentication Overview](https://cloud.google.com/docs/authentication/).
  
* `Ksonnet 0.12`
  We use [Ksonnet](https://ksonnet.io/) to write Kubernetes jobs in a declarative manner to be run
  on top of Kubeflow.

# Getting Started

To get started, follow the instructions below.

**NOTE**: We will assume that the Kubeflow cluster is available at `kubeflow.example.com`. Make sure
you replace this with the true FQDN of your Kubeflow cluster in any subsequent instructions.

* Spawn a new JupyterLab instance inside the Kubeflow cluster by pointing your browser to
  **https://kubeflow.example.com/hub** and clicking "**Start My Server**".

* In the **Image** text field, enter `gcr.io/kubeflow-images-public/kubeflow-codelab-notebook:v20180808-v0.2-22-gcfdcb12`.
  This image contains all the pre-requisites needed for the demo.
  
* Once spawned, you should be redirected to the Jupyter Notebooks UI.

* Spawn a new Terminal and run
  ```
  $ git clone --branch=master --depth=1 https://github.com/kubeflow/examples
  ```
  This will create an examples folder. It is safe to close the terminal now.
  
* Navigate back to the Jupyter Notebooks UI and navigate to `examples/code_search`. Open
  the Jupyter notebook `code-search.ipynb` and follow it along.

# Acknowledgements

This project derives from [hamelsmu/code_search](https://github.com/hamelsmu/code_search).
