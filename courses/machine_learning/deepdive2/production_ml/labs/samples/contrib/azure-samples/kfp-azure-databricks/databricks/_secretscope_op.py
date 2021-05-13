import json
from kfp.dsl import ResourceOp

class CreateSecretScopeOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Secret Scope creation
    resource template.

    Example:

        import databricks

        databricks.CreateSecretScopeOp(
            name="createsecretscope",
            scope_name="test-secretscope",
            spec={
                "initial_manage_permission": "users",
                "secrets": [
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
                ],
                "acls": [
                    {
                        "principal": "user@foo.com",
                        "permission": "READ"
                    }
                ]
            }
        )

        databricks.CreateSecretScopeOp(
            name="createsecretscope",
            scope_name="test-secretscope",
            initial_manage_permission="users",
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
            ],
            acls=[
                {
                    "principal": "user@foo.com",
                    "permission": "READ"
                }
            ]
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 scope_name: str = None,
                 spec: {} = None,
                 initial_manage_principal: str = None,
                 secrets: {} = None,
                 acls: {} = None):
        """Create a new instance of CreateSecretScopeOp.

        Args:
            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, scope_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            scope_name: A name for the Secret Scope.
                If k8s_name is provided, this will be ignored.
            spec: Full specification of the Secret Scope to create.
            initial_manage_principal: The principal that is initially granted MANAGE permission to
                the created scope.
            secrets: Secrets that will be stored at this scope.
            acls: ACLs that will be set on this scope.

        Raises:

            ValueError: If no k8s resource name or Secret Scope name are provided.
        """

        if not spec:
            spec = {}

        if initial_manage_principal:
            spec["initial_manage_permission"] = initial_manage_principal
        if secrets:
            spec["secrets"] = secrets
        if acls:
            spec["acls"] = acls

        k8s_name = k8s_name or scope_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a scope_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "SecretScope",
                "metadata": {
                    "name": k8s_name
                },
                "spec": spec
            },
            action="create",
            success_condition="status.secretscope.name",
            attribute_outputs={
                "name": "{.metadata.name}",
                "secretscope_name": "{.status.secretscope.name}",
                "secretscope_backend_type": "{.status.secretscope.backend_type}",
                "secret_in_cluster_available": "{.status.secretinclusteravailable}"
            },
            name=name)

    @classmethod
    def from_json_spec(cls,
                       name: str = None,
                       k8s_name: str = None,
                       scope_name: str = None,
                       json_spec: str = None):
        """Create a new instance of CreateSecretScopeOp from a json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, scope_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            scope_name: A name for the Secret Scope.
                If k8s_name is provided, this will be ignored.
            json_spec: Full specification of the Secret Scope to create in json format.
        """

        spec = json.loads(json_spec)
        return cls(name=name, k8s_name=k8s_name, scope_name=scope_name, spec=spec)

    @classmethod
    def from_file_name(cls,
                       name: str = None,
                       k8s_name: str = None,
                       scope_name: str = None,
                       file_name: str = None):
        """Create a new instance of CreateSecretScopeOp from a file with json specification.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, scope_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            scope_name: A name for the Secret Scope.
                If k8s_name is provided, this will be ignored.
            json_spec_file_name: Name of the file containing the full specification of the Secret
                Scope to create in json format.

        Raises:

            ValueError: if the file name doesn't exist.
        """

        with open(file_name) as json_file:
            spec = json.loads(json_file.read())
        return cls(name=name, k8s_name=k8s_name, scope_name=scope_name, spec=spec)

    @property
    def resource(self):
        """`Resource` object that represents the `resource` property in
        `io.argoproj.workflow.v1alpha1.Template`.
        """
        return self._resource

class DeleteSecretScopeOp(ResourceOp):
    """Represents an Op which will be translated into a Databricks Secret Scope deletion
    resource template.

    Example:

        import databricks

        databricks.DeleteSecretScopeOp(
            name = "deletesecretscope",
            scope_name = "test-secretscope"
        )
    """

    def __init__(self,
                 name: str = None,
                 k8s_name: str = None,
                 scope_name: str = None):
        """Create a new instance of DeleteSecretScopeOp.

        Args:

            name: The name of the pipeline Op.
                It does not have to be unique within a pipeline
                because the pipeline will generate a new unique name in case of a conflict.
            k8s_name = The name of the k8s resource which will be submitted to the cluster.
                If no k8s_name is provided, scope_name will be used as the resource name.
                This name is DNS-1123 subdomain name and must consist of lower case alphanumeric
                characters, '-' or '.', and must start and end with an alphanumeric character.
            scope_name: The name of the Secret Scope.
                If k8s_name is provided, this will be ignored.

        Raises:

            ValueError: If no k8s resource name or Secret Scope name are provided.
        """

        k8s_name = k8s_name or scope_name
        if not k8s_name:
            raise ValueError("You need to provide a k8s_name or a scope_name.")

        super().__init__(
            k8s_resource={
                "apiVersion": "databricks.microsoft.com/v1alpha1",
                "kind": "SecretScope",
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