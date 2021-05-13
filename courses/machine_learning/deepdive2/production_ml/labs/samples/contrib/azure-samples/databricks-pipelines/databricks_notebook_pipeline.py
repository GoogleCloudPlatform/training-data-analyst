"""Import a notebook into a Databricks workspace and submit a job run to execute it in a cluster.
Notebook will accept some parameters and access a file in DBFS and some secrets in a secret scope.
"""
from pathlib import Path
import base64
import kfp.dsl as dsl
import kfp.compiler as compiler
import databricks

def create_dbfsblock(block_name):
    return databricks.CreateDbfsBlockOp(
        name="createdbfsblock",
        block_name=block_name,
        data="QWxlamFuZHJvIENhbXBvcyBNYWdlbmNpbw==",
        path="/data/foo.txt"
    )

def create_secretscope(scope_name):
    return databricks.CreateSecretScopeOp(
        name="createsecretscope",
        scope_name=scope_name,
        initial_manage_principal="users",
        secrets=[
            {
                "key": "string-secret",
                "string_value": "helloworld"
            },
            {
                "key": "byte-secret",
                "byte_value": "aGVsbG93b3JsZA=="
            },
            {
                "key": "ref-secret",
                "value_from": {
                    "secret_key_ref": {
                        "name": "mysecret",
                        "key": "username"
                    }
                }
            }
        ]
    )

def import_workspace_item(item_name, user):
    current_path = Path(__file__).parent
    notebook_file_name = current_path.joinpath("notebooks", "ScalaExampleNotebook")
    notebook = open(notebook_file_name).read().encode("utf-8")
    notebook_base64 = base64.b64encode(notebook)
    return databricks.ImportWorkspaceItemOp(
        name="importworkspaceitem",
        item_name=item_name,
        content=notebook_base64,
        path=f"/Users/{user}/ScalaExampleNotebook",
        language="SCALA",
        file_format="SOURCE"
    )

def create_cluster(cluster_name):
    return databricks.CreateClusterOp(
        name="createcluster",
        cluster_name=cluster_name,
        spark_version="5.3.x-scala2.11",
        node_type_id="Standard_D3_v2",
        spark_conf={
            "spark.speculation": "true"
        },
        num_workers=2
    )

def create_job(job_name, cluster_id, user):
    return databricks.CreateJobOp(
        name="createjob",
        job_name=job_name,
        existing_cluster_id=cluster_id,
        notebook_task={
            "notebook_path": f"/Users/{user}/ScalaExampleNotebook"
        }
    )

def submit_run(run_name, job_name, parameter1, parameter2):
    return databricks.SubmitRunOp(
        name="submitrun",
        run_name=run_name,
        job_name=job_name,
        notebook_params={
            "param1": parameter1,
            "param2": parameter2
        }
    )

def delete_run(run_name):
    return databricks.DeleteRunOp(
        name="deleterun",
        run_name=run_name
    )

def delete_job(job_name):
    return databricks.DeleteJobOp(
        name="deletejob",
        job_name=job_name
    )

def delete_cluster(cluster_name):
    return databricks.DeleteClusterOp(
        name="deletecluster",
        cluster_name=cluster_name
    )

def delete_workspace_item(item_name):
    return databricks.DeleteWorkspaceItemOp(
        name="deleteworkspaceitem",
        item_name=item_name
    )

def delete_secretscope(scope_name):
    return databricks.DeleteSecretScopeOp(
        name="deletesecretscope",
        scope_name=scope_name
    )

def delete_dbfsblock(block_name):
    return databricks.DeleteDbfsBlockOp(
        name="deletedbfsblock",
        block_name=block_name
    )

@dsl.pipeline(
    name="Databrick",
    description="A toy pipeline that runs a sample notebook in a Databricks cluster."
)
def calc_pipeline(
        dbfsblock_name="test-block",
        secretescope_name="test-scope",
        workspaceitem_name="test-item",
        cluster_name="test-cluster",
        job_name="test-job",
        run_name="test-run",
        user="user@foo.com",
        parameter1="38",
        parameter2="43"):
    create_dbfsblock_task = create_dbfsblock(dbfsblock_name)
    create_secretscope_task = create_secretscope(secretescope_name)
    import_workspace_item_task = import_workspace_item(workspaceitem_name, user)
    create_cluster_task = create_cluster(cluster_name)
    create_job_task = create_job(job_name, create_cluster_task.outputs["cluster_id"], user)
    submit_run_task = submit_run(run_name, job_name, parameter1, parameter2)
    submit_run_task.after(create_dbfsblock_task)
    submit_run_task.after(create_secretscope_task)
    submit_run_task.after(import_workspace_item_task)
    submit_run_task.after(create_job_task)
    delete_run_task = delete_run(run_name)
    delete_run_task.after(submit_run_task)
    delete_job_task = delete_job(job_name)
    delete_job_task.after(delete_run_task)
    delete_cluster_task = delete_cluster(cluster_name)
    delete_cluster_task.after(delete_job_task)
    delete_workspace_item_task = delete_workspace_item(workspaceitem_name)
    delete_workspace_item_task.after(submit_run_task)
    delete_secretscope_task = delete_secretscope(secretescope_name)
    delete_secretscope_task.after(submit_run_task)
    delete_dbfsblock_task = delete_dbfsblock(dbfsblock_name)
    delete_dbfsblock_task.after(submit_run_task)

if __name__ == "__main__":
    compiler.Compiler()._create_and_write_workflow(
        pipeline_func=calc_pipeline,
        package_path=__file__ + ".tar.gz")
