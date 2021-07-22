"""Submit a one-time Run with implicit cluster creation to Databricks."""
import kfp.dsl as dsl
import kfp.compiler as compiler
import databricks

def submit_run(run_name, parameter):
    return databricks.SubmitRunOp(
        name="submitrun",
        run_name=run_name,
        new_cluster={
            "spark_version":"5.3.x-scala2.11",
            "node_type_id": "Standard_D3_v2",
            "num_workers": 2
        },
        libraries=[{"jar": "dbfs:/docs/sparkpi.jar"}],
        spark_jar_task={
            "main_class_name": "org.apache.spark.examples.SparkPi",
            "parameters": [parameter]
        }
    )

def delete_run(run_name):
    return databricks.DeleteRunOp(
        name="deleterun",
        run_name=run_name
    )

@dsl.pipeline(
    name="DatabricksRun",
    description="A toy pipeline that computes an approximation to pi with Azure Databricks."
)
def calc_pipeline(run_name="test-run", parameter="10"):
    submit_run_task = submit_run(run_name, parameter)
    delete_run_task = delete_run(run_name)
    delete_run_task.after(submit_run_task)

if __name__ == "__main__":
    compiler.Compiler()._create_and_write_workflow(
        pipeline_func=calc_pipeline,
        package_path=__file__ + ".tar.gz")
