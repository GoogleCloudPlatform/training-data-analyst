import unittest
from pathlib import Path
import kfp
from kfp.dsl import PipelineParam
from databricks import CreateSecretScopeOp, DeleteSecretScopeOp

class TestCreateSecretScopeOp(unittest.TestCase):

    def test_databricks_create_secretscope_without_k8s_or_scope_name(self):
        def my_pipeline():
            CreateSecretScopeOp(
                name="createsecretscope",
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
                ],
                acls=[
                    {
                        "principal": "user@foo.com",
                        "permission": "READ"
                    }
                ]
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_create_secretscope(self):
        def my_pipeline():
            scope_name = "test-secretscope"
            initial_manage_principal = "users"
            secrets = [
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
            acls = [
                {
                    "principal": "user@foo.com",
                    "permission": "READ"
                }
            ]

            expected_spec = {
                "initial_manage_permission": initial_manage_principal,
                "secrets": secrets,
                "acls": acls
            }

            res = CreateSecretScopeOp(
                name="createsecretscope",
                scope_name=scope_name,
                initial_manage_principal=initial_manage_principal,
                secrets=secrets,
                acls=acls
            )
            
            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_secretscope_with_spec(self):
        def my_pipeline():
            scope_name = "test-secretscope"
            spec = {
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

            res = CreateSecretScopeOp(
                name="createsecretscope",
                scope_name=scope_name,
                spec=spec
            )

            self.assert_res(res, spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_secretscope_with_spec_and_extra_args(self):
        def my_pipeline():
            scope_name = "test-secretscope"
            acls = [
                {
                    "principal": "user@foo.com",
                    "permission": "READ"
                }
            ]
            spec = {
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
                ]
            }

            expected_spec = {
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
                "acls": acls
            }

            res = CreateSecretScopeOp(
                name="createsecretscope",
                scope_name=scope_name,
                spec=spec,
                acls=acls
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_secretscope_with_json_spec(self):
        def my_pipeline():
            scope_name = "test-secretscope"
            json_spec = """
            {
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
            """

            expected_spec = {
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

            res = CreateSecretScopeOp.from_json_spec(
                name="createsecretscope",
                scope_name=scope_name,
                json_spec=json_spec
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_secretscope_with_json_file_spec(self):
        def my_pipeline():
            scope_name = "test-secretscope"
            current_path = Path(__file__).parent
            json_spec_file_name = current_path.joinpath("secretscope_spec.json")

            expected_spec = {
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

            res = CreateSecretScopeOp.from_file_name(
                name="createsecretscope",
                scope_name=scope_name,
                file_name=json_spec_file_name
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def assert_res(self, res, expected_spec):
        self.assertEqual(res.name, "createsecretscope")
        self.assertEqual(res.resource.action, "create")
        self.assertEqual(
            res.resource.success_condition,
            "status.secretscope.name"
        )
        self.assertEqual(res.resource.failure_condition, None)
        self.assertEqual(res.resource.manifest, None)
        expected_attribute_outputs = {
            "name": "{.metadata.name}",
            "secretscope_name": "{.status.secretscope.name}",
            "secretscope_backend_type": "{.status.secretscope.backend_type}",
            "secret_in_cluster_available": "{.status.secretinclusteravailable}",
            "manifest": "{}"
        }
        self.assertEqual(res.attribute_outputs, expected_attribute_outputs)
        expected_outputs = {
            "name": PipelineParam(name="name", op_name=res.name),
            "secretscope_name":
                PipelineParam(name="secretscope_name", op_name=res.name),
            "secretscope_backend_type":
                PipelineParam(name="secretscope_backend_type", op_name=res.name),
            "secret_in_cluster_available":
                PipelineParam(name="secret_in_cluster_available", op_name=res.name),
            "manifest": PipelineParam(name="manifest", op_name=res.name)
        }
        self.assertEqual(res.outputs, expected_outputs)
        self.assertEqual(
            res.output,
            PipelineParam(name="name", op_name=res.name)
        )
        self.assertEqual(res.dependent_names, [])
        self.assertEqual(res.k8s_resource["kind"], "SecretScope")
        self.assertEqual(res.k8s_resource["metadata"]["name"], "test-secretscope")
        self.assertEqual(res.k8s_resource["spec"], expected_spec)

class TestDeleteSecretScopeOp(unittest.TestCase):

    def test_databricks_delete_secretscope_without_k8s_or_scope_name(self):
        def my_pipeline():
            DeleteSecretScopeOp(
                name="deletesecretscope"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_delete_secretscope(self):
        def my_pipeline():

            res = DeleteSecretScopeOp(
                name="deletesecretscope",
                scope_name="test-secretscope"
            )

            self.assertEqual(res.name, "deletesecretscope")
            self.assertEqual(res.resource.action, "delete")
            self.assertEqual(res.resource.success_condition, None)
            self.assertEqual(res.resource.failure_condition, None)
            self.assertEqual(res.resource.manifest, None)
            self.assertEqual(res.attribute_outputs, {})
            self.assertEqual(res.outputs, {})
            self.assertEqual(res.output, None)
            self.assertEqual(res.dependent_names, [])
            self.assertEqual(res.k8s_resource["kind"], "SecretScope")
            self.assertEqual(res.k8s_resource["metadata"]["name"], "test-secretscope")

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

if __name__ == '__main__':
    unittest.main()