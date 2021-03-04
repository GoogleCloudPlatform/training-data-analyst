import json
from kfp.dsl import ResourceOp

class ImportWorkspaceItemOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Workspace Item import
    resource template.

    Example:

        import databricks

        databricks.ImportWorkspaceItemOp(
            name="importworkspaceitem",
            item_name="test-item",
            spec={
                "content": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook",
                "language": "SCALA",
                "format": "SOURCE"
            }
        )

        databricks.ImportWorkspaceItemOp(
            name="importworkspaceitem",
            item_name="test-item",
            content="cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
            path="/Users/user@foo.com/ScalaExampleNotebook",
            language="SCALA",
            file_format="SOURCE"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 item_name: str = None,
                 spec: {} = None,
                 content: str = None,
                 path: str = None,
                 language: str = None,
                 file_format: str = None):
        """Create a new instance of ImportWorkspaceItemOp.

        Args:
            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, item_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            item_name: A name for the Workspace Item.
                If k8s_name is provided, this will be ignored.
            spec: Full specification of the Workspace Item to import.
            content: The base64-encoded content.
                This has a limit of 10 MB.
            path: The absolute path of the notebook or directory.
                Importing directory is only support for DBC format.
            language: The language.
                If format is set to SOURCE, this field is required; otherwise, it will be ignored.
            file_format: This specifies the format of the file to be imported.
                By default, this is SOURCE. However it may be one of: SOURCE, HTML, JUPYTER, DBC.
                The value is case sensitive.

        Raises:

            ValueError: If no k8s resource name or Workspace Item name are provided.
        """

        if not spec:
            spec = {}

        if content:
            spec["content"] = content
        if path:
            spec["path"] = path
        if language:
            spec["language"] = language
        if file_format:
            spec["format"] = file_format

        k8s_name = k8s_name or item_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a item_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "WorkspaceItem",
                "metadata": {
                    "name": k8s_name
                },
                "spec": spec
            },
            action="create",
            success_condition="status.object_hash",
            attribute_outputs={
                "name": "{.metadata.name}",
                "object_hash": "{.status.object_hash}",
                "object_language": "{.status.object_info.language}",
                "object_type": "{.status.object_info.object_type}",
                "object_path": "{.status.object_info.path}"
            },
            name=name)

    @classmethod
    def from_json_spec(cls,
                       name: str = None,
                       k8s_name: str = None,
                       item_name: str = None,
                       json_spec: str = None):
        """Create a new instance of ImportWorkspaceItemOp from a json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, item_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            item_name: A name for the Workspace Item.
                If k8s_name is provided, this will be ignored.
            json_spec: Full specification of the Workspace Item to import in json format.
        """

        spec = json.loads(json_spec)
        return cls(name=name, k8s_name=k8s_name, item_name=item_name, spec=spec)

    @classmethod
    def from_file_name(cls,
                       name: str = None,
                       k8s_name: str = None,
                       item_name: str = None,
                       file_name: str = None):
        """Create a new instance of ImportWorkspaceItemOp from a file with json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, item_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            item_name: A name for the Workspace Item.
                If k8s_name is provided, this will be ignored.
            json_spec: Name of the file containing the full specification of the Workspace Item to
                import in json format.

        Raises:

            ValueError: if the file name doesn't exist.
        """

        with open(file_name) as json_file:
            spec = json.loads(json_file.read())
        return cls(name=name, k8s_name=k8s_name, item_name=item_name, spec=spec)

    @property
    def resource(self):
        """`Resource` object that represents the `resource` property in
        `io.argoproj.workflow.v1alpha1.Template`.
        """
        return self._resource

class DeleteWorkspaceItemOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Workspace Item deletion
    resource template.

    Example:

        import databricks

        databricks.DeleteWorkspaceItemOp(
            name="deleteworkspaceitem",
            item_name="test-item"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 item_name: str = None):
        """Create a new instance of DeleteWorkspaceItemOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, item_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            item_name: The name of the Workspace Item.
                If k8s_name is provided, this will be ignored.

        Raises:

            ValueError: If no k8s resource name or Workspace Item name are provided.
        """

        k8s_name = k8s_name or item_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a item_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "WorkspaceItem",
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
