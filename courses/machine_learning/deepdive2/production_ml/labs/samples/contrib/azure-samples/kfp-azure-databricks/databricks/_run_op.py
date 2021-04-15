import json
from kfp.dsl import ResourceOp

class SubmitRunOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Run submission
    resource template.

    Examples:

        import databricks

        databricks.SubmitRunOp(
            name="submitrun",
            run_name="test-run",
            spec={
                "new_cluster": {
                    "spark_version":"5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "spark_submit_task": {
                    "parameters": [
                        "--class",
                        "org.apache.spark.examples.SparkPi",
                        "dbfs:/docs/sparkpi.jar",
                        "10"
                    ]
                }
            }
        )

        databricks.SubmitRunOp(
            name="submitrun",
            run_name="test-run",
            new_cluster={
                "spark_version":"5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            },
            libraries=[
                {
                    "jar": "dbfs:/my-jar.jar"
                },
                {
                    "maven": {
                        "coordinates": "org.jsoup:jsoup:1.7.2"
                    }
                }
            ],
            spark_jar_task={
                "main_class_name": "com.databricks.ComputeModels"
            }
        )

        databricks.SubmitRunOp(
            name="submitrun",
            run_name="test-run",
            existing_cluster_id="cluster-id",
            spark_python_task={
                "python_file": "dbfs:/docs/pi.py",
                "parameters": ["10"]
            }
        )

        databricks.SubmitRunOp(
            name="submitrun",
            run_name="test-run",
            job_name="test-job",
            jar_params=["param1", "param2"]
        )

        databricks.SubmitRunOp.from_json_spec(
            name="submitrun",
            run_name="test-run",
            json_spec=_JSON_SPEC
        )

        databricks.SubmitRunOp.from_file_name(
            name="submitrun",
            run_name="test-run",
            file_name="run_spec.json"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 run_name: str = None,
                 spec: {} = None,
                 job_name: str = None,
                 jar_params: {} = None,
                 python_params: {} = None,
                 spark_submit_params: {} = None,
                 notebook_params: {} = None,
                 existing_cluster_id: str = None,
                 new_cluster: {} = None,
                 libraries: {} = None,
                 spark_jar_task: {} = None,
                 spark_python_task: {} = None,
                 spark_submit_task: {} = None,
                 notebook_task: {} = None,
                 timeout_seconds: int = None):
        """Create a new instance of SubmitRunOp.
        
        Args:
            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, run_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            run_name: A name for the Run.
            spec: Full specification of the Run to submit.
            job_name: The name of an existing Job to run.
            jar_params: A list of parameters for jobs with JAR task.
            python_params: A list of parameters for jobs with Python tasks.
            spark_submit_params: A list of parameters for jobs with spark submit task.
            notebook_params: A map from keys to values for jobs with notebook task.
            existing_cluster_id: The ID of an existing cluster that will be used for all runs of
                this job.
            new_cluster: A description of a cluster that will be created for each run
            libraries: An optional list of libraries to be installed on the cluster that will
                execute the job.
            spark_jar_task: Indicates that this job should run a JAR.
            spark_python_task: Indicates that this job should run a Python file.
            spark_submit_task: Indicates that this job should run spark submit script.
            notebook_task: Indicates that this job should run a notebook.
            timeout_seconds: An optional timeout applied to each run of this job.
                The default behavior is to have no timeout.

        Raises:

            ValueError: If no k8s resource name or Run name are provided.
        """

        if not spec:
            spec = {}

        if run_name:
            spec["run_name"] = run_name
        if job_name:
            spec["job_name"] = job_name
        if jar_params:
            spec["jar_params"] = jar_params
        if python_params:
            spec["python_params"] = python_params
        if spark_submit_params:
            spec["spark_submit_params"] = spark_submit_params
        if notebook_params:
            spec["notebook_params"] = notebook_params
        if new_cluster:
            spec["new_cluster"] = new_cluster
        if existing_cluster_id:
            spec["existing_cluster_id"] = existing_cluster_id
        if spark_jar_task:
            spec["spark_jar_task"] = spark_jar_task
        if spark_python_task:
            spec["spark_python_task"] = spark_python_task
        if spark_submit_task:
            spec["spark_submit_task"] = spark_submit_task
        if notebook_task:
            spec["notebook_task"] = notebook_task
        if libraries:
            spec["libraries"] = libraries
        if timeout_seconds:
            spec["timeout_seconds"] = timeout_seconds

        if not k8s_name and "run_name" in spec:
            k8s_name = spec["run_name"]
        elif not k8s_name:
            raise ValueError("You need to provide a k8s_name or a run_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "Run",
                "metadata": {
                    "name": k8s_name
                },
                "spec": spec
            },
            action="create",
            success_condition=("status.metadata.state.life_cycle_state in "
                               "(TERMINATED, SKIPPED, INTERNAL_ERROR)"),
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
            },
            name=name)

    @classmethod
    def from_json_spec(cls,
                       name: str = None,
                       k8s_name: str = None,
                       run_name: str = None,
                       json_spec: str = None):
        """Create a new instance of SubmitRunOp from a json specification.

        Args:

            name: The name of the Op.
                It does not have to be unique within a pipeline
                because the pipeline will generates a unique new name in case of conflicts.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, run_name will be used as the resource name.
            run_name: A name for the Run.
            json_spec: Full specification of the Run to submit in json format.
        """

        spec = json.loads(json_spec)
        return cls(name=name, k8s_name=k8s_name, run_name=run_name, spec=spec)

    @classmethod
    def from_file_name(cls,
                       name: str = None,
                       k8s_name: str = None,
                       run_name: str = None,
                       file_name: str = None):
        """Create a new instance of SubmitRunOp from a file with a json specification.

        Args:

            name: The name of the Op.
                It does not have to be unique within a pipeline
                because the pipeline will generates a unique new name in case of conflicts.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, run_name will be used as the resource name.
            run_name: A name for the Run.
            json_spec_file_name: Name of the file containing the full specification of the Run
                to submit in json format.

        Raises:

            ValueError: if the file name doesn't exist.
        """

        with open(file_name) as json_file:
            spec = json.loads(json_file.read())
        return cls(name=name, k8s_name=k8s_name, run_name=run_name, spec=spec)

    @property
    def resource(self):
        """`Resource` object that represents the `resource` property in
        `io.argoproj.workflow.v1alpha1.Template`.
        """
        return self._resource

class DeleteRunOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Run deletion resource
    template.

    Example:

        import databricks

        databricks.DeleteRunOp(
            name="deleterun",
            run_name="test-run"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 run_name: str = None):
        """Create a new instance of DeleteRunOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, run_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            run_name: The name of the Run.
                If k8s_name is provided, this will be ignored.

        Raises:

            ValueError: If no k8s resource name or Run name are provided.
        """

        k8s_name = k8s_name or run_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a run_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "Run",
                "metadata": {
                    "name": k8s_name
                }
            },
            action="delete",
            name=name)

    @property
    def resource(self):
        """`Resource` object that represents the `resource` property in
        `io.argoproj.workflow.v1alpha1.Template`.
        """
        return self._resource
