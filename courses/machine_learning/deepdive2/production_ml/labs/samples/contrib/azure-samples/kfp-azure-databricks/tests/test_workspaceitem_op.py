import unittest
from pathlib import Path
import kfp
from kfp.dsl import PipelineParam
from databricks import ImportWorkspaceItemOp, DeleteWorkspaceItemOp

class TestImportWorkspaceItemOp(unittest.TestCase):

    def test_databricks_import_workspaceitem_without_k8s_or_item_name(self):
        def my_pipeline():
            ImportWorkspaceItemOp(
                name="importworkspaceitem",
                content="cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                path="/Users/user@foo.com/ScalaExampleNotebook",
                language="SCALA",
                file_format="SOURCE"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_import_workspaceitem(self):
        def my_pipeline():
            item_name = "test-item"
            content = "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK"
            path = "/Users/user@foo.com/ScalaExampleNotebook"
            language = "SCALA"
            file_format = "SOURCE"

            expected_spec = {
                "content": content,
                "path": path,
                "language": language,
                "format": file_format
            }

            res = ImportWorkspaceItemOp(
                name="importworkspaceitem",
                item_name=item_name,
                content=content,
                path=path,
                language=language,
                file_format=file_format
            )
            
            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_import_workspaceitem_with_spec(self):
        def my_pipeline():
            item_name = "test-item"
            spec = {
                "content": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook",
                "language": "SCALA",
                "format": "SOURCE"
            }

            res = ImportWorkspaceItemOp(
                name="importworkspaceitem",
                item_name=item_name,
                spec=spec
            )

            self.assert_res(res, spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_import_workspaceitem_with_spec_and_extra_args(self):
        def my_pipeline():
            item_name = "test-item"
            content = "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK"
            spec = {
                "path": "/Users/user@foo.com/ScalaExampleNotebook",
                "language": "SCALA",
                "format": "SOURCE"
            }

            expected_spec = {
                "content": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook",
                "language": "SCALA",
                "format": "SOURCE"
            }

            res = ImportWorkspaceItemOp(
                name="importworkspaceitem",
                item_name=item_name,
                spec=spec,
                content=content
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_import_workspaceitem_with_json_spec(self):
        def my_pipeline():
            item_name = "test-item"
            json_spec = """
            {
                "content": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook",
                "language": "SCALA",
                "format": "SOURCE"
            }
            """

            expected_spec = {
                "content": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook",
                "language": "SCALA",
                "format": "SOURCE"
            }

            res = ImportWorkspaceItemOp.from_json_spec(
                name="importworkspaceitem",
                item_name=item_name,
                json_spec=json_spec
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_import_workspaceitem_with_json_file_spec(self):
        def my_pipeline():
            item_name = "test-item"
            current_path = Path(__file__).parent
            json_spec_file_name = current_path.joinpath("workspaceitem_spec.json")

            expected_spec = {
                "content": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook",
                "language": "SCALA",
                "format": "SOURCE"
            }

            res = ImportWorkspaceItemOp.from_file_name(
                name="importworkspaceitem",
                item_name=item_name,
                file_name=json_spec_file_name
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def assert_res(self, res, expected_spec):
        self.assertEqual(res.name, "importworkspaceitem")
        self.assertEqual(res.resource.action, "create")
        self.assertEqual(res.resource.success_condition, "status.object_hash")
        self.assertEqual(res.resource.failure_condition, None)
        self.assertEqual(res.resource.manifest, None)
        expected_attribute_outputs = {
            "name": "{.metadata.name}",
            "object_hash": "{.status.object_hash}",
            "object_language": "{.status.object_info.language}",
            "object_type": "{.status.object_info.object_type}",
            "object_path": "{.status.object_info.path}",
            "manifest": "{}"
        }                
        self.assertEqual(res.attribute_outputs, expected_attribute_outputs)
        expected_outputs = {
            "name": PipelineParam(name="name", op_name=res.name),
            "object_hash": PipelineParam(name="object_hash", op_name=res.name),
            "object_language": PipelineParam(name="object_language", op_name=res.name),
            "object_type": PipelineParam(name="object_type", op_name=res.name),
            "object_path": PipelineParam(name="object_path", op_name=res.name),
            "manifest": PipelineParam(name="manifest", op_name=res.name)
        }
        self.assertEqual(res.outputs, expected_outputs)
        self.assertEqual(
            res.output,
            PipelineParam(name="name", op_name=res.name)
        )
        self.assertEqual(res.dependent_names, [])
        self.assertEqual(res.k8s_resource["kind"], "WorkspaceItem")
        self.assertEqual(res.k8s_resource["metadata"]["name"], "test-item")
        self.assertEqual(res.k8s_resource["spec"], expected_spec)

class TestDeleteWorkspaceItemOp(unittest.TestCase):

    def test_databricks_delete_workspaceitem_without_k8s_or_item_name(self):
        def my_pipeline():
            DeleteWorkspaceItemOp(
                name="deleteworkspaceitem"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_delete_workspaceitem(self):
        def my_pipeline():

            res = DeleteWorkspaceItemOp(
                name="deleteworkspaceitem",
                item_name="test-item"
            )

            self.assertEqual(res.name, "deleteworkspaceitem")
            self.assertEqual(res.resource.action, "delete")
            self.assertEqual(res.resource.success_condition, None)
            self.assertEqual(res.resource.failure_condition, None)
            self.assertEqual(res.resource.manifest, None)
            self.assertEqual(res.attribute_outputs, {})
            self.assertEqual(res.outputs, {})
            self.assertEqual(res.output, None)
            self.assertEqual(res.dependent_names, [])
            self.assertEqual(res.k8s_resource["kind"], "WorkspaceItem")
            self.assertEqual(res.k8s_resource["metadata"]["name"], "test-item")

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

if __name__ == '__main__':
    unittest.main()