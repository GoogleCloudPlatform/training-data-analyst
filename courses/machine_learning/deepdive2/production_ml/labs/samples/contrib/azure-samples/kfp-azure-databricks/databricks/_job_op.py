import json
from kfp.dsl import ResourceOp

class CreateJobOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Job creation
    resource template.

    Example:

        import databricks

        databricks.CreateJobOp(
            name="createjob",
            job_name="test-job",
            spec={
                "new_cluster" : {
                    "spark_version":"5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "libraries" : [
                    {
                        "jar": 'dbfs:/my-jar.jar'
                    },
                    {
                        "maven": {
                            "coordinates": 'org.jsoup:jsoup:1.7.2'
                        }
                    }
                ],
                "timeout_seconds" : 3600,
                "max_retries": 1,
                "schedule":{
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles",
                },
                "spark_jar_task": {
                    "main_class_name": "com.databricks.ComputeModels",
                },
            }
        )

        databricks.CreateJobOp(
            name="createjob",
            job_name="test-job",
            new_cluster={
                "spark_version":"5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            },
            libraries=[
                {
                    "jar": 'dbfs:/my-jar.jar'
                },
                {
                    "maven": {
                        "coordinates": 'org.jsoup:jsoup:1.7.2'
                    }
                }
            ],
            timeout_seconds=3600,
            max_retries=1,
            schedule={
                "quartz_cron_expression": "0 15 22 ? * *",
                "timezone_id": "America/Los_Angeles",
            },
            spark_jar_task={
                "main_class_name": "com.databricks.ComputeModels",
            }
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 job_name: str = None,
                 spec: {} = None,
                 existing_cluster_id: str = None,
                 new_cluster: {} = None,
                 libraries: {} = None,
                 spark_jar_task: {} = None,
                 spark_python_task: {} = None,
                 spark_submit_task: {} = None,
                 notebook_task: {} = None,
                 timeout_seconds: int = None,
                 max_retries: int = None,
                 min_retry_interval_millis: int = None,
                 retry_on_timeout: bool = None,
                 schedule: {} = None,
                 max_concurrent_runs: int = None,
                 email_notifications: {} = None):

        """Create a new instance of CreateJobOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, job_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            job_name: A name for the Job.
            spec: Full specification of the Job to create.
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
            max_retries: An optional maximum number of times to retry an unsuccessful run.
                The value -1 means to retry indefinitely and the value 0 means to never retry.
                The default behavior is to never retry.
            min_retry_interval_millis: An optional minimal interval in milliseconds between the
                start of the failed run and the subsequent retry run.
                The default behavior is that unsuccessful runs are immediately retried.
            retry_on_timeout: An optional policy to specify whether to retry a job when it times
                out.
                The default behavior is to not retry on timeout.
            schedule: An optional periodic schedule for this job.
                The default behavior is that the job runs when triggered by clicking Run Now in the
                Jobs UI or sending an API request to runNow.
            max_concurrent_runs: An optional maximum allowed number of concurrent runs of the job.
            email_notifications: An optional set of email addresses notified when runs of this job
                begin and complete and when this job is deleted.

        Raises:
            ValueError: If no k8s resource name or Job name are provided.
        """

        if not spec:
            spec = {}

        if job_name:
            spec["name"] = job_name
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
        if max_retries:
            spec["max_retries"] = max_retries
        if min_retry_interval_millis:
            spec["min_retry_interval_millis"] = min_retry_interval_millis
        if retry_on_timeout:
            spec["retry_on_timeout"] = retry_on_timeout
        if schedule:
            spec["schedule"] = schedule
        if max_concurrent_runs:
            spec["max_concurrent_runs"] = max_concurrent_runs
        if email_notifications:
            spec["email_notifications"] = email_notifications

        if not k8s_name and "name" in spec:
            k8s_name = spec["name"]
        elif not k8s_name:
            raise ValueError("You need to provide a k8s_name or a job_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "Djob",
                "metadata": {
                    "name": k8s_name
                },
                "spec": spec
            },
            action="create",
            success_condition="status.job_status.job_id > 0",
            attribute_outputs={
                "name": "{.metadata.name}",
                "job_id": "{.status.job_status.job_id}",
                "job_name": "{.status.job_status.settings.name}"
            },
            name=name)

    @classmethod
    def from_json_spec(cls,
                       name: str = None,
                       k8s_name: str = None,
                       job_name: str = None,
                       json_spec: str = None):
        """Create a new instance of CreateJobOp from a json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, job_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            job_name: A name for the Job.
            json_spec: Full specification of the Job to create in json format.
        """

        spec = json.loads(json_spec)
        return cls(name=name, k8s_name=k8s_name, job_name=job_name, spec=spec)

    @classmethod
    def from_file_name(cls,
                       name: str = None,
                       k8s_name: str = None,
                       job_name: str = None,
                       file_name: str = None):
        """Create a new instance of CreateJobOp from a file with json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, job_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            job_name: A name for the Job.
            json_spec_file_name: Name of the file containing the full specification of the Job to
                create in json format.

        Raises:

            ValueError: if the file name doesn't exist.
        """

        with open(file_name) as json_file:
            spec = json.loads(json_file.read())
        return cls(name=name, k8s_name=k8s_name, job_name=job_name, spec=spec)

    @property
    def resource(self):
        """`Resource` object that represents the `resource` property in
        `io.argoproj.workflow.v1alpha1.Template`.
        """
        return self._resource

class DeleteJobOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Spark Job deletion
    resource template.

    Example:

        import databricks

        databricks.DeleteJobOp(
            name = "deletejob",
            job_name = "test-job"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 job_name: str = None):
        """Create a new instance of DeleteJobOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, job_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            job_name: the name of the Job.
                If k8s_name is provided, this will be ignored.

        Raises:

            ValueError: If no k8s resource name or Job name are provided.
        """

        k8s_name = k8s_name or job_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a job_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "Djob",
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
