# Introduction to Azure Databricks for Kubeflow Pipelines

Azure Databricks Package provides a set of [Kubeflow Pipeline](https://www.kubeflow.org/docs/pipelines/) 
Tasks (Ops) which let us manipulate [Databricks](https://azure.microsoft.com/services/databricks/) 
resources using the [Azure Databricks Operator for Kubernetes](
https://github.com/microsoft/azure-databricks-operator). This makes the user experience much nicer,
and less error prone, than using the [ResourceOp](
https://www.kubeflow.org/docs/pipelines/sdk/manipulate-resources/#resourceop) to manipulate
these Databricks resources.

## Supported Ops

- CreateClusterOp, to create a cluster in Databricks.
- DeleteClusterOp, to delete a cluster created with CreateClusterOp.
- CreateJobOp, to create a Spark job in Databricks.
- DeleteJobOp, to delete a job created with CreateJobOp.
- SubmitRunOp, to submit a job run in Databricks.
- DeleteRunOp, to delete a run submitted with SubmitRunOp.
- CreateSecretScopeOp, to create a secret scope in Databricks.
- DeleteSecretScopeOp, to delete a secret scope created with CreateSecretScopeOp.
- ImportWorkspaceItemOp, to import an item into a Databricks Workspace.
- DeleteWorkspaceItemOp, to delete an item imported with ImportWorkspaceItemOp.
- CreateDbfsBlockOp, to create Dbfs Block in Databricks.
- DeleteDbfsBlockOp, to delete Dbfs Block created with CreateDbfsBlockOp.

For each of these there are two ways a Kubeflow user can create the Ops:
1) By passing the complete Databricks spec for the Op within a Python Dictionary.
2) By using named parameters.

## Setup

1) [Create an Azure Databricks workspace](
    https://docs.microsoft.com/en-us/azure/databricks/getting-started/try-databricks?toc=https%3A%2F%2Fdocs.microsoft.com%2Fen-us%2Fazure%2Fazure-databricks%2FTOC.json&bc=https%3A%2F%2Fdocs.microsoft.com%2Fen-us%2Fazure%2Fbread%2Ftoc.json#--step-2-create-an-azure-databricks-workspace)
2) [Deploy the Azure Databricks Operator for Kubernetes](
    https://github.com/microsoft/azure-databricks-operator/blob/master/docs/deploy.md)
3) [Install the Kubeflow Pipelines SDK](https://www.kubeflow.org/docs/pipelines/sdk/install-sdk/)
4) Install Databricks Package:
```
pip install -e "git+https://github.com/kubeflow/pipelines#egg=kfp-azure-databricks&subdirectory=samples/contrib/azure-samples/kfp-azure-databricks" --upgrade
```
To uninstall Databricks Package use:
```
pip uninstall kfp-azure-databricks
```

## Example

The following sample pipeline will submit a one-time job run with implicit cluster creation to Azure 
Databricks:

```python
import kfp.dsl as dsl
import databricks

@dsl.pipeline(
    name="DatabricksRun",
    description="A toy pipeline that computes an approximation to pi with Databricks."
)
def calc_pipeline(run_name="test-run", parameter="10"):
    submit_run_task = databricks.SubmitRunOp(
        name="submitrun",
        run_name=run_name,
        new_cluster={
            "spark_version": "5.3.x-scala2.11",
            "node_type_id": "Standard_D3_v2",
            "num_workers": 2
        },
        libraries=[{"jar": "dbfs:/docs/sparkpi.jar"}],
        spark_jar_task={
            "main_class_name": "org.apache.spark.examples.SparkPi",
            "parameters": [parameter]
        }
    )

    delete_run_task = databricks.DeleteRunOp(
        name="deleterun",
        run_name=run_name
    )
    delete_run_task.after(submit_run_task)    
```

This sample is based on the following article: [Create a spark-submit job](
https://docs.databricks.com/dev-tools/api/latest/examples.html#create-and-run-a-jar-job), which 
points to the library *sparkpi.jar*. You may upload the library to [Databricks 
File System](https://docs.microsoft.com/en-us/azure/databricks/data/databricks-file-system) using 
[DBFS CLI](https://docs.microsoft.com/en-us/azure/databricks/dev-tools/databricks-cli#dbfs-cli).

## Example using ResourceOp

This sample pipeline shows the code that would be required to submit a one-time job run with 
implicit cluster creation to Azure Databricks, but using ResourceOp instead of this package:

```python
import kfp.dsl as dsl
import kfp.compiler as compiler

@dsl.pipeline(
    name="DatabricksRun",
    description="A toy pipeline that computes an approximation to pi with Databricks."
)
def calc_pipeline(run_name="test-run", parameter="10"):
    submit_run_task = dsl.ResourceOp(
        name="submitrun",
        k8s_resource={
            "apiVersion": "databricks.microsoft.com/v1alpha1",
            "kind": "Run",
            "metadata": {
                "name":run_name,
            },
            "spec":{
                "run_name": run_name,
                "new_cluster": {
                    "spark_version": "5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "libraries": [{"jar": "dbfs:/docs/sparkpi.jar"}],
                "spark_jar_task": {
                    "main_class_name": "com.databricks.ComputeModels",
                    "parameters": [parameter]
                }
            },
        },
        action="create",
        success_condition="status.metadata.state.life_cycle_state in (TERMINATED, SKIPPED, INTERNAL_ERROR)",
        attribute_outputs={
            "name": "{.metadata.name}",
            "job_id": "{.status.metadata.job_id}",
            "number_in_job": "{.status.metadata.number_in_job}",
            "run_id": "{.status.metadata.run_id}",
            "run_name": "{.status.metadata.run_name}",
            "life_cycle_state": "{.status.metadata.state.life_cycle_state}",
            "result_state": "{.status.metadata.state.result_state}",
            "notebook_output_result": "{.status.notebook_output.result}",
            "notebook_output_truncated": "{.status.notebook_output.truncated}",
            "error": "{.status.error}"
        }
    )

    delete_run_task = dsl.ResourceOp(
        name="deleterun",
        k8s_resource={
            "apiVersion": "databricks.microsoft.com/v1alpha1",
            "kind": "Run",
            "metadata": {
                "name": run_name
            }
        },
        action="delete"
    )
    delete_run_task.after(submit_run_task)
```

## Additional examples

More sample pipelines can be found in folder 
[samples/contrib/azure-samples/databricks-pipelines](../databricks-pipelines/) and in the tests of 
this package: [samples/contrib/azure-samples/kfp-azure-databricks/tests](./tests/).

## Additional information
- [Kubeflow Pipelines](https://www.kubeflow.org/docs/pipelines/) 
- [Azure Databricks documentation](https://docs.microsoft.com/azure/azure-databricks/) 
- [Azure Databricks Operator for Kubernetes](https://github.com/microsoft/azure-databricks-operator)
- [Golang SDK for DataBricks REST API 2.0 and Azure DataBricks REST API 2.0](
    https://github.com/xinsnake/databricks-sdk-golang), used by Azure Databricks Operator.
- [Databricks REST API 2.0](https://docs.databricks.com/dev-tools/api/latest/index.html)
- [Azure Databricks REST API 2.0](
    https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/)

The following articles provide information on the supported spec fields for the supported Databricks
Ops:  
- Cluster Ops: [Azure Databricks Cluster API](
    https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/clusters)
- Job Ops: [Azure Databricks Jobs API](
    https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/jobs)
- Run Ops: [Azure Databricks Jobs API - Runs Submit](
    https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/jobs#--runs-submit)
- Secret Scope Ops: [Azure Databricks Secrets API](
    https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/secrets)
- Workspace Item Ops: [Azure Databricks Workspace API](
    https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/workspace)
- DbfsBlock Ops: [Azure Databricks DBFS API](
    https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/dbfs)

