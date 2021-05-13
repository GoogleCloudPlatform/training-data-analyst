import unittest
from pathlib import Path
import kfp
from kfp.dsl import PipelineParam
from databricks import CreateClusterOp, DeleteClusterOp

class TestCreateClusterOp(unittest.TestCase):

    def test_databricks_create_cluster_without_k8s_or_cluster_name(self):
        def my_pipeline():
            CreateClusterOp(
                name="createcluster",
                spark_version="5.3.x-scala2.11",
                node_type_id="Standard_D3_v2",
                spark_conf={
                    "spark.speculation": "true"
                },
                num_workers=2
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_create_cluster(self):
        def my_pipeline():
            cluster_name = "test-cluster"
            spark_version = "5.3.x-scala2.11"
            node_type_id = "Standard_D3_v2"
            spark_conf = {
                "spark.speculation": "true"
            }
            num_workers = 2

            expected_spec = {
                "cluster_name": cluster_name,
                "spark_version": spark_version,
                "node_type_id": node_type_id,
                "spark_conf": spark_conf,
                "num_workers": num_workers
            }

            res = CreateClusterOp(
                name="createcluster",
                cluster_name=cluster_name,
                spark_version=spark_version,
                node_type_id=node_type_id,
                spark_conf=spark_conf,
                num_workers=num_workers
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_autoscaling_cluster(self):
        def my_pipeline():
            cluster_name = "test-cluster"
            spark_version = "5.3.x-scala2.11"
            node_type_id = "Standard_D3_v2"
            autoscale = {
                "min_workers": 2,
                "max_workers": 50
            }

            expected_spec = {
                "cluster_name": cluster_name,
                "spark_version":spark_version,
                "node_type_id": node_type_id,
                "autoscale": autoscale
            }

            res = CreateClusterOp(
                name="createcluster",
                cluster_name=cluster_name,
                spark_version=spark_version,
                node_type_id=node_type_id,
                autoscale=autoscale
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_cluster_with_spec(self):
        def my_pipeline():
            spec = {
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "spark_conf": {
                    "spark.speculation": "true"
                },
                "num_workers": 2
            }

            res = CreateClusterOp(
                name="createcluster",
                cluster_name="test-cluster",
                spec=spec
            )

            self.assert_res(res, spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_cluster_with_spec_and_extra_args(self):
        def my_pipeline():
            spec = {
                "spark_version":"5.3.x-scala2.11",
                "spark_conf": {
                    "spark.speculation": "true"
                }
            }

            expected_spec = {
                "cluster_name": "test-cluster",
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "spark_conf": {
                    "spark.speculation": "true"
                },
                "num_workers": 2
            }                

            res = CreateClusterOp(
                name="createcluster",
                cluster_name="test-cluster",
                spec=spec,
                node_type_id="Standard_D3_v2",
                num_workers=2
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)        

    def test_databricks_create_cluster_with_json_spec(self):
        def my_pipeline():
            cluster_name = "test-cluster"
            json_spec = """
            {
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "spark_conf": {
                    "spark.speculation": "true"
                },
                "num_workers": 2
            }
            """

            expected_spec = {
                "cluster_name": cluster_name,
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "spark_conf": {
                    "spark.speculation": "true"
                },
                "num_workers": 2
            }

            res = CreateClusterOp.from_json_spec(
                name="createcluster",
                cluster_name=cluster_name,
                json_spec=json_spec
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_cluster_with_json_file_spec(self):
        def my_pipeline():
            cluster_name = "test-cluster"
            current_path = Path(__file__).parent
            json_spec_file_name = current_path.joinpath("cluster_spec.json")

            expected_spec = {
                "cluster_name": cluster_name,
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "spark_conf": {
                    "spark.speculation": "true"
                },
                "num_workers": 2
            }

            res = CreateClusterOp.from_file_name(
                name="createcluster",
                cluster_name=cluster_name,
                file_name=json_spec_file_name
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def assert_res(self, res, expected_spec):
        self.assertEqual(res.name, "createcluster")
        self.assertEqual(res.resource.action, "create")
        self.assertEqual(
            res.resource.success_condition,
            "status.cluster_info.state in (RUNNING, TERMINATED, UNKNOWN)"
        )
        self.assertEqual(res.resource.failure_condition, None)
        self.assertEqual(res.resource.manifest, None)
        expected_attribute_outputs = {
            "name": "{.metadata.name}",
            "cluster_id": "{.status.cluster_info.cluster_id}",
            "cluster_name": "{.status.cluster_info.cluster_name}",
            "state": "{.status.cluster_info.state}",
            "manifest": "{}"
        }
        self.assertEqual(res.attribute_outputs, expected_attribute_outputs)
        expected_outputs = {
            "name": PipelineParam(name="name", op_name=res.name),
            "cluster_id": PipelineParam(name="cluster_id", op_name=res.name),
            "cluster_name": PipelineParam(name="cluster_name", op_name=res.name),
            "state": PipelineParam(name="state", op_name=res.name),
            "manifest": PipelineParam(name="manifest", op_name=res.name)
        }
        self.assertEqual(res.outputs, expected_outputs)
        self.assertEqual(
            res.output,
            PipelineParam(name="name", op_name=res.name)
        )
        self.assertEqual(res.dependent_names, [])
        self.assertEqual(res.k8s_resource["kind"], "Dcluster")
        self.assertEqual(res.k8s_resource["metadata"]["name"], "test-cluster")
        self.assertEqual(res.k8s_resource["spec"], expected_spec)

class TestDeleteClusterOp(unittest.TestCase):

    def test_databricks_delete_cluster_without_k8s_or_cluster_name(self):
        def my_pipeline():
            DeleteClusterOp(
                name="deletecluster"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_delete_cluster(self):
        def my_pipeline():

            res = DeleteClusterOp(
                name="deletecluster",
                cluster_name="test-cluster"
            )

            self.assertEqual(res.name, "deletecluster")
            self.assertEqual(res.resource.action, "delete")
            self.assertEqual(res.resource.success_condition, None)
            self.assertEqual(res.resource.failure_condition, None)
            self.assertEqual(res.resource.manifest, None)
            self.assertEqual(res.attribute_outputs, {})
            self.assertEqual(res.outputs, {})
            self.assertEqual(res.output, None)
            self.assertEqual(res.dependent_names, [])
            self.assertEqual(res.k8s_resource["kind"], "Dcluster")
            self.assertEqual(res.k8s_resource["metadata"]["name"], "test-cluster")

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

if __name__ == '__main__':
    unittest.main()
