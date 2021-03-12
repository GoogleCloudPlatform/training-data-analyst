import unittest
from pathlib import Path
import kfp
from kfp.dsl import PipelineParam
from databricks import CreateDbfsBlockOp, DeleteDbfsBlockOp

class TestCreateDbfsBlockOp(unittest.TestCase):

    def test_databricks_createdbfsblock_without_k8s_or_block_name(self):
        def my_pipeline():
            CreateDbfsBlockOp(
                name="createdbfsitem",
                data="cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                path="/Users/user@foo.com/ScalaExampleNotebook"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_createdbfsblock(self):
        def my_pipeline():
            block_name = "createdbfsitem"
            data = "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK"
            path = "/Users/user@foo.com/ScalaExampleNotebook"
            

            expected_spec = {
                "path": path,
                "data": data
            }

            res = CreateDbfsBlockOp(
                name="createdbfsitem",
                block_name=block_name,
                path=path,
                data=data
            )
            
            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_createdbfsblock_with_spec(self):
        def my_pipeline():
            block_name = "createdbfsitem"
            spec = {
                "data": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook"
            }

            res = CreateDbfsBlockOp(
                name="createdbfsitem",
                block_name=block_name,
                spec=spec
            )

            self.assert_res(res, spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_createdbfsblock_with_spec_and_extra_args(self):
        def my_pipeline():
            block_name = "createdbfsitem"
            data = "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK"
            spec = {
                "path": "/Users/user@foo.com/ScalaExampleNotebook"
            }

            expected_spec = {
                "data": data,
                "path": "/Users/user@foo.com/ScalaExampleNotebook"
            }

            res = CreateDbfsBlockOp(
                name="createdbfsitem",
                block_name=block_name,
                data=data,
                spec=spec
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_createdbfsblock_with_json_spec(self):
        def my_pipeline():
            block_name = "createdbfsitem"
            json_spec = """
            {
                "data": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook"
            }
            """

            expected_spec = {
                "data": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/Users/user@foo.com/ScalaExampleNotebook"
            }

            res = CreateDbfsBlockOp.from_json_spec(
                name="createdbfsitem",
                block_name=block_name,
                json_spec=json_spec
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_createdbfsblock_with_json_file_spec(self):
        def my_pipeline():
            block_name = "createdbfsitem"
            current_path = Path(__file__).parent
            json_spec_file_name = current_path.joinpath("dbfsblock_spec.json")

            expected_spec = {
                "data": "cHJpbnQoImhlbGxvLCB3b3JsZCIpCgoK",
                "path": "/data/foo.txt"
            }

            res = CreateDbfsBlockOp.from_file_name(
                name="createdbfsitem",
                block_name=block_name,
                file_name=json_spec_file_name
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def assert_res(self, res, expected_spec):
        self.assertEqual(res.name, "createdbfsitem")
        self.assertEqual(res.resource.action, "create")
        self.assertEqual(res.resource.success_condition, "status.file_hash")
        self.assertEqual(res.resource.failure_condition, None)
        self.assertEqual(res.resource.manifest, None)
        expected_attribute_outputs = {
            "name": "{.metadata.name}",
            "file_info_path": "{.status.file_info.path}",
            "file_info_is_dir": "{.status.file_info.is_dir}",
            "file_info_file_size": "{.status.file_info.file_size}",
            "file_hash": "{.status.file_hash}",
            "manifest": "{}"
        }                
        self.assertEqual(res.attribute_outputs, expected_attribute_outputs)
        expected_outputs = {
            "name": PipelineParam(name="name", op_name=res.name),
            "file_info_path": PipelineParam(name="file_info_path", op_name=res.name),
            "file_info_is_dir": PipelineParam(name="file_info_is_dir", op_name=res.name),
            "file_info_file_size": PipelineParam(name="file_info_file_size", op_name=res.name),
            "file_hash": PipelineParam(name="file_hash", op_name=res.name),
            "manifest": PipelineParam(name="manifest", op_name=res.name)
        }
        self.assertEqual(res.outputs, expected_outputs)
        self.assertEqual(
            res.output,
            PipelineParam(name="name", op_name=res.name)
        )
        self.assertEqual(res.dependent_names, [])
        self.assertEqual(res.k8s_resource["kind"], "DbfsBlock")
        self.assertEqual(res.k8s_resource["metadata"]["name"], "createdbfsitem")
        self.assertEqual(res.k8s_resource["spec"], expected_spec)

class TestDeletedbfsblockOp(unittest.TestCase):

    def test_databricks_delete_dbfsblock_without_k8s_or_block_name(self):
        def my_pipeline():
            DeleteDbfsBlockOp(
                name="deletedbfsblock"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_delete_dbfsblock(self):
        def my_pipeline():

            res = DeleteDbfsBlockOp(
                name="deletedbfsblock",
                block_name="createdbfsitem"
            )

            self.assertEqual(res.name, "deletedbfsblock")
            self.assertEqual(res.resource.action, "delete")
            self.assertEqual(res.resource.success_condition, None)
            self.assertEqual(res.resource.failure_condition, None)
            self.assertEqual(res.resource.manifest, None)
            self.assertEqual(res.attribute_outputs, {})
            self.assertEqual(res.outputs, {})
            self.assertEqual(res.output, None)
            self.assertEqual(res.dependent_names, [])
            self.assertEqual(res.k8s_resource["kind"], "DbfsBlock")
            self.assertEqual(res.k8s_resource["metadata"]["name"], "createdbfsitem")

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

if __name__ == '__main__':
    unittest.main()