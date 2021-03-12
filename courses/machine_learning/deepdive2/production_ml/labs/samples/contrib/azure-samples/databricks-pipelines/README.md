# Introduction to Azure Databricks pipeline samples

This folder contains several [Kubeflow Pipeline](https://www.kubeflow.org/docs/pipelines/) samples 
which show how to manipulate [Databricks](https://azure.microsoft.com/services/databricks/) 
resources using the [Azure Databricks for Kubeflow Pipelines](
../kfp-azure-databricks/) package.

## Setup

1) [Create an Azure Databricks workspace](
    https://docs.microsoft.com/en-us/azure/databricks/getting-started/try-databricks?toc=https%3A%2F%2Fdocs.microsoft.com%2Fen-us%2Fazure%2Fazure-databricks%2FTOC.json&bc=https%3A%2F%2Fdocs.microsoft.com%2Fen-us%2Fazure%2Fbread%2Ftoc.json#--step-2-create-an-azure-databricks-workspace)
2) [Deploy the Azure Databricks Operator for Kubernetes](
    https://github.com/microsoft/azure-databricks-operator/blob/master/docs/deploy.md)
3) Some samples reference 'sparkpi.jar' library. This library can be found here: [Create and run a 
jar job](https://docs.databricks.com/dev-tools/api/latest/examples.html#create-and-run-a-jar-job). 
Upload it to [Databricks File System](
https://docs.microsoft.com/en-us/azure/databricks/data/databricks-file-system) using e.g. [DBFS 
CLI](https://docs.microsoft.com/en-us/azure/databricks/dev-tools/databricks-cli#dbfs-cli).
4) Some samples that use CreateSecretScopeOp reference a secret in Kubernetes. This secret must be
created before running these pipelines. For example:
```bash
kubectl create secret generic -n kubeflow mysecret --from-literal=username=alex 
```
5) [Install the Kubeflow Pipelines SDK](https://www.kubeflow.org/docs/pipelines/sdk/install-sdk/)
6) Install Azure Databricks for Kubeflow Pipelines package:
```
pip install -e "git+https://github.com/kubeflow/pipelines#egg=kfp-azure-databricks&subdirectory=samples/contrib/azure-samples/kfp-azure-databricks" --upgrade
```
To uninstall Azure Databricks for Kubeflow Pipelines package use:
```
pip uninstall kfp-azure-databricks
```

## Testing the pipelines

Install the requirements:
```bash
pip install --upgrade -r requirements.txt
```
Compile a pipeline with any of the following commands:
```bash
dsl-compile --py databricks_run_pipeline.py --output databricks_run_pipeline.py.tar.gz
# Or
python3 databricks_run_pipeline.py
# Or
python3 pipeline_cli.py compile databricks_run_pipeline.py
```
Then run the compiled pipeline in Kubeflow:
```bash
python3 pipeline_cli.py run databricks_run_pipeline.py.tar.gz http://localhost:8080/pipeline '{"run_name":"test-run","parameter":"10"}'
```
Or compile and run a pipeline in Kubeflow with a single command:
```bash
python3 pipeline_cli.py compile_run databricks_run_pipeline.py http://localhost:8080/pipeline '{"run_name":"test-run","parameter":"10"}'
```