import json
from kfp.dsl import ResourceOp

class CreateDbfsBlockOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks DbfsBlock  Create
    resource template.

    Example:

        import databricks

        databricks.CreateDbfsBlockOp(
            name="createdbfsblock",
            block_name="test-item",
            spec={
                "data": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/data/foo.txt",
            }
        )

        databricks.CreateDbfsBlockOp(
            name="createdbfsblock",
            block_name="test-item",
            data="cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
            path="/data/foo.txt",
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 block_name: str = None,
                 spec: {} = None,
                 path: str = None,
                 data: str = None):
        """Create a new instance of CreateDbfsBlockOp.

        Args:
            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, block_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            block_name: A name for the DbfsBlock.
                If k8s_name is provided, this will be ignored.
            data: The base64-encoded content.
                This has a limit of 10 MB.
            path: The absolute path of the file.
                Importing directory is only support for DBC format.

        Raises:

            ValueError: If no k8s resource name or DbfsBlock name are provided.
        """

        if not spec:
            spec = {}      
        if path:
            spec["path"] = path
        if data:
            spec["data"] = data

        k8s_name = k8s_name or block_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a block_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "DbfsBlock",
                "metadata": {
                    "name": k8s_name
                },
                "spec": spec
            },
            action="create",
            success_condition="status.file_hash",
            attribute_outputs={
                "name": "{.metadata.name}",
                "file_info_path": "{.status.file_info.path}",
                "file_info_is_dir": "{.status.file_info.is_dir}",
                "file_info_file_size": "{.status.file_info.file_size}",
                "file_hash": "{.status.file_hash}"
            },
            name=name)

    @classmethod
    def from_json_spec(cls,
                       name: str = None,
                       k8s_name: str = None,
                       block_name: str = None,
                       json_spec: str = None):
        """Create a new instance of CreateDbfsBlockOp from a json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, block_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            block_name: A name for the DbfsBlock Item.
                If k8s_name is provided, this will be ignored.
            json_spec: Full specification of the DbfsBlock Item to import in json format.
        """

        spec = json.loads(json_spec)
        return cls(name=name, k8s_name=k8s_name, block_name=block_name, spec=spec)

    @classmethod
    def from_file_name(cls,
                       name: str = None,
                       k8s_name: str = None,
                       block_name: str = None,
                       file_name: str = None):
        """Create a new instance of CreateDbfsBlockOp from a file with json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, block_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            block_name: A name for the DbfsBlock Item.
                If k8s_name is provided, this will be ignored.
            json_spec: Name of the file containing the full specification of the DbfsBlock Item to
                import in json format.

        Raises:

            ValueError: if the file name doesn't exist.
        """

        with open(file_name) as json_file:
            spec = json.loads(json_file.read())
        return cls(name=name, k8s_name=k8s_name, block_name=block_name, spec=spec)

    @property
    def resource(self):
        """`Resource` object that represents the `resource` property in
        `io.argoproj.workflow.v1alpha1.Template`.
        """
        return self._resource

class DeleteDbfsBlockOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks DbfsBlock Item deletion
    resource template.

    Example:

        import databricks

        databricks.DeleteDbfsBlockOp(
            name="deletedbfsblock",
            block_name="test-item"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 block_name: str = None):
        """Create a new instance of DeleteDbfsBlockOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, block_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            block_name: The name of the DbfsBlock Item.
                If k8s_name is provided, this will be ignored.

        Raises:

            ValueError: If no k8s resource name or Dbfs Item name are provided.
        """

        k8s_name = k8s_name or block_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a block_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "DbfsBlock",
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
