import json
from kfp.dsl import ResourceOp

class CreateClusterOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Cluster creation resource
    template.

    Examples:

        import databricks

        databricks.CreateClusterOp(
            name="createcluster",
            cluster_name="test-cluster",
            spec={
                "spark_version":"5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "spark_conf": {
                    "spark.speculation": "true"
                },
                "num_workers": 2
            }
        )

        databricks.CreateClusterOp(
            name="createcluster",
            cluster_name="test-cluster",
            spark_version="5.3.x-scala2.11",
            node_type_id="Standard_D3_v2",
            spark_conf={
                "spark.speculation": "true"
            },
            num_workers=2
        )

        databricks.CreateClusterOp(
            name="createcluster",
            cluster_name="test-cluster",
            spark_version="5.3.x-scala2.11",
            node_type_id="Standard_D3_v2",
            autoscale={
                "min_workers": 2,
                "max_workers": 50
            }
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 cluster_name: str = None,
                 spec: {} = None,
                 num_workers: int = None,
                 autoscale: {} = None,
                 spark_version: str = None,
                 spark_conf: {} = None,
                 node_type_id: str = None,
                 driver_node_type_id: str = None,
                 custom_tags: {} = None,
                 cluster_log_conf: {} = None,
                 init_scripts: {} = None,
                 spark_env_vars: {} = None,
                 autotermination_minutes: int = None,
                 instance_pool_id: str = None):
        """Create a new instance of CreateClusterOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, cluster_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            cluster_name: Cluster name requested by the user.
            spec: Full specification of the Databricks cluster to create.
            num_workers: Number of worker nodes that this cluster should have.
            autoscale: Parameters needed in order to automatically scale clusters up and down based
                on load.
            spark_version: The runtime version of the cluster.
            spark_conf: An object containing a set of optional, user-specified Spark configuration
                key-value pairs.
            node_type_id: This field encodes, through a single value, the resources available to
                each of the Spark nodes in this cluster.
            driver_node_type_id: The node type of the Spark driver.
            custom_tags: Additional tags for cluster resources.
            cluster_log_conf: The configuration for delivering Spark logs to a long-term storage
                destination.
            init_scripts: The configuration for storing init scripts.
            spark_env_vars: An object containing a set of optional, user-specified environment
                variable key-value pairs.
            autotermination_minutes: Automatically terminates the cluster after it is inactive for
                this time in minutes. If not set, this cluster will not be automatically terminated.
            instance_pool_id: The optional ID of the instance pool to which the cluster belongs.

        Raises:

            ValueError: If no k8s resource name or Cluster name are provided.
        """

        if not spec:
            spec = {}

        if cluster_name:
            spec["cluster_name"] = cluster_name
        if num_workers:
            spec["num_workers"] = num_workers
        if autoscale:
            spec["autoscale"] = autoscale
        if spark_version:
            spec["spark_version"] = spark_version
        if spark_conf:
            spec["spark_conf"] = spark_conf
        if node_type_id:
            spec["node_type_id"] = node_type_id
        if driver_node_type_id:
            spec["driver_node_type_id"] = driver_node_type_id
        if custom_tags:
            spec["custom_tags"] = custom_tags
        if cluster_log_conf:
            spec["cluster_log_conf"] = cluster_log_conf
        if init_scripts:
            spec["init_scripts"] = init_scripts
        if spark_env_vars:
            spec["spark_env_vars"] = spark_env_vars
        if autotermination_minutes:
            spec["autotermination_minutes"] = autotermination_minutes
        if instance_pool_id:
            spec["instance_pool_id"] = instance_pool_id

        if not k8s_name and "cluster_name" in spec:
            k8s_name = spec["cluster_name"]
        elif not k8s_name:
            raise ValueError("You need to provide a k8s_name or a cluster_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "Dcluster",
                "metadata": {
                    "name": k8s_name,
                },
                "spec": spec,
            },
            action="create",
            success_condition="status.cluster_info.state in (RUNNING, TERMINATED, UNKNOWN)",
            attribute_outputs={
                "name": "{.metadata.name}",
                "cluster_id": "{.status.cluster_info.cluster_id}",
                "cluster_name": "{.status.cluster_info.cluster_name}",
                "state": "{.status.cluster_info.state}"
            },
            name=name)

    @classmethod
    def from_json_spec(cls,
                       name: str = None,
                       k8s_name: str = None,
                       cluster_name: str = None,
                       json_spec: str = None):
        """Create a new instance of CreateClusterOp from a json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, cluster_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            cluster_name: Cluster name requested by the user.
            json_spec: Full specification of the Databricks cluster to create in json format.
        """

        spec = json.loads(json_spec)
        return cls(name=name, k8s_name=k8s_name, cluster_name=cluster_name, spec=spec)

    @classmethod
    def from_file_name(cls,
                       name: str = None,
                       k8s_name: str = None,
                       cluster_name: str = None,
                       file_name: str = None):
        """Create a new instance of CreateClusterOp from a file with a json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, cluster_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            cluster_name: Cluster name requested by the user.
            json_spec_file_name: Name of the file containing the full specification of the
                Databricks cluster to create in json format.

        Raises:

            ValueError: if the file name doesn't exist.
        """

        with open(file_name) as json_file:
            spec = json.loads(json_file.read())
        return cls(name=name, k8s_name=k8s_name, cluster_name=cluster_name, spec=spec)

    @property
    def resource(self):
        """`Resource` object that represents the `resource` property in
        `io.argoproj.workflow.v1alpha1.Template`.
        """
        return self._resource

class DeleteClusterOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Cluster deletion resource
    template.

    Example:

        import databricks

        databricks.DeleteClusterOp(
            name="deletecluster",
            cluster_name="test-cluster"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 cluster_name: str = None):
        """Create a new instance of DeleteClusterOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, cluster_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            cluster_name: The name of the cluster.
                If k8s_name is provided, this will be ignored.

        Raises:

            ValueError: If no k8s resource name or Cluster name are provided.
        """

        k8s_name = k8s_name or cluster_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a cluster_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "Dcluster",
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
