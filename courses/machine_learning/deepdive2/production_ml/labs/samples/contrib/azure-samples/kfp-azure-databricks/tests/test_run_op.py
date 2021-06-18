import unittest
from pathlib import Path
import kfp
from kfp.dsl import PipelineParam
from databricks import SubmitRunOp, DeleteRunOp

class TestSubmitRunOp(unittest.TestCase):

    def test_databricks_submit_run_without_k8s_or_run_name(self):
        def my_pipeline():
            SubmitRunOp(
                name="submitrun",
                new_cluster={
                    "spark_version":"5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                libraries=[
                    {"jar": "dbfs:/my-jar.jar"},
                    {"maven": {"coordinates": "org.jsoup:jsoup:1.7.2"}}
                ],
                spark_jar_task={
                    "main_class_name": "com.databricks.ComputeModels"
                }
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_submit_run_with_job_name_and_jar_params(self):
        def my_pipeline():
            run_name = "test-run"
            job_name = "test-job"
            jar_params = ["param1", "param2"]

            expected_spec = {
                "run_name": run_name,
                "job_name": job_name,
                "jar_params": jar_params
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                job_name=job_name,
                jar_params=jar_params
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_job_name_and_python_params(self):
        def my_pipeline():
            run_name = "test-run"
            job_name = "test-job"
            python_params = ["john doe", "35"]

            expected_spec = {
                "run_name": run_name,
                "job_name": job_name,
                "python_params": python_params
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                job_name=job_name,
                python_params=python_params
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_job_name_and_spark_submit_params(self):
        def my_pipeline():
            run_name = "test-run"
            job_name = "test-job"
            spark_submit_params = ["--class", "org.apache.spark.examples.SparkPi"]

            expected_spec = {
                "run_name": run_name,
                "job_name": job_name,
                "spark_submit_params": spark_submit_params
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                job_name=job_name,
                spark_submit_params=spark_submit_params
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_job_name_and_notebook_params(self):
        def my_pipeline():
            run_name = "test-run"
            job_name = "test-job"
            notebook_params = {
                "dry-run": "true",
                "oldest-time-to-consider": "1457570074236"
            }

            expected_spec = {
                "run_name": run_name,
                "job_name": job_name,
                "notebook_params": notebook_params
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                job_name=job_name,
                notebook_params=notebook_params
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_new_cluster_and_spark_jar_task(self):
        def my_pipeline():
            run_name = "test-run"
            new_cluster = {
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            }
            libraries = [
                {"jar": "dbfs:/my-jar.jar"},
                {"maven": {"coordinates": "org.jsoup:jsoup:1.7.2"}}
            ]
            spark_jar_task = {
                "main_class_name": "com.databricks.ComputeModels"
            }

            expected_spec = {
                "run_name": run_name,
                "new_cluster": new_cluster,
                "libraries": libraries,
                "spark_jar_task": spark_jar_task
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                new_cluster=new_cluster,
                libraries=libraries,
                spark_jar_task=spark_jar_task
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_new_cluster_and_spark_python_task(self):
        def my_pipeline():
            run_name = "test-run"
            new_cluster = {
                "spark_version":"5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            }
            spark_python_task = {
                "python_file": "dbfs:/docs/pi.py",
                "parameters": [
                    "10"
                ]
            }

            expected_spec = {
                "run_name": run_name,
                "new_cluster": new_cluster,
                "spark_python_task": spark_python_task
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                new_cluster=new_cluster,
                spark_python_task=spark_python_task
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_new_cluster_and_spark_submit_task(self):
        def my_pipeline():
            run_name = "test-run"
            new_cluster = {
                "spark_version":"5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            }
            spark_submit_task = {
                "parameters": [
                    "--class",
                    "org.apache.spark.examples.SparkPi",
                    "dbfs:/docs/sparkpi.jar",
                    "10"
                ]
            }

            expected_spec = {
                "run_name": run_name,
                "new_cluster": new_cluster,
                "spark_submit_task":spark_submit_task
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                new_cluster=new_cluster,
                spark_submit_task=spark_submit_task
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_existing_cluster_and_notebook_task(self):
        def my_pipeline():
            run_name = "test-run"
            existing_cluster_id = "1201-my-cluster"
            notebook_task = {
                "notebook_path": "/Users/donald@duck.com/my-notebook"
            }
            timeout_seconds = 120

            expected_spec = {
                "run_name": run_name,
                "existing_cluster_id": existing_cluster_id,
                "notebook_task": notebook_task,
                "timeout_seconds": timeout_seconds
            }

            res = SubmitRunOp(
                name="submitrun",
                run_name=run_name,
                existing_cluster_id=existing_cluster_id,
                notebook_task=notebook_task,
                timeout_seconds=timeout_seconds
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_spec(self):
        def my_pipeline():
            spec = {
                "run_name": "test-run",
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

            res = SubmitRunOp(
                name="submitrun",
                spec=spec
            )

            self.assert_res(res, spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_spec_and_extra_args(self):
        def my_pipeline():
            spark_submit_task = {
                "parameters": [
                    "--class",
                    "org.apache.spark.examples.SparkPi",
                    "dbfs:/docs/sparkpi.jar",
                    "10"
                ]
            }
            spec = {
                "run_name": "test-run",
                "new_cluster": {
                    "spark_version":"5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "spark_submit_task": {
                    "parameters": [
                        "--class"
                    ]
                }
            }

            expected_spec = {
                "run_name": "test-run",
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

            res = SubmitRunOp(
                name="submitrun",
                spec=spec,
                spark_submit_task=spark_submit_task
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_json_spec(self):
        def my_pipeline():
            run_name = "test-run"
            json_spec = """
            {
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
            """

            expected_spec = {
                "run_name": run_name,
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

            res = SubmitRunOp.from_json_spec(
                name="submitrun",
                run_name=run_name,
                json_spec=json_spec
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_submit_run_with_json_file_spec(self):
        def my_pipeline():
            run_name = "test-run"
            current_path = Path(__file__).parent
            json_spec_file_name = current_path.joinpath("run_spec.json")

            expected_spec = {
                "run_name": run_name,
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

            res = SubmitRunOp.from_file_name(
                name="submitrun",
                run_name=run_name,
                file_name=json_spec_file_name
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def assert_res(self, res, expected_spec):
        self.assertEqual(res.name, "submitrun")
        self.assertEqual(res.resource.action, "create")
        self.assertEqual(
            res.resource.success_condition,
            "status.metadata.state.life_cycle_state in (TERMINATED, SKIPPED, INTERNAL_ERROR)"
        )
        self.assertEqual(res.resource.failure_condition, None)
        self.assertEqual(res.resource.manifest, None)
        expected_attribute_outputs = {
            "name": "{.metadata.name}",
            "job_id": "{.status.metadata.job_id}",
            "number_in_job": "{.status.metadata.number_in_job}",
            "run_id": "{.status.metadata.run_id}",
            "run_name": "{.status.metadata.run_name}",
            "life_cycle_state": "{.status.metadata.state.life_cycle_state}",
            "result_state": "{.status.metadata.state.result_state}",
            "notebook_output_result": "{.status.notebook_output.result}",
            "notebook_output_truncated": "{.status.notebook_output.truncated}",
            "error": "{.status.error}",
            "manifest": "{}"
        }
        self.assertEqual(res.attribute_outputs, expected_attribute_outputs)
        expected_outputs = {
            "name": PipelineParam(name="name", op_name=res.name),
            "job_id": PipelineParam(name="job_id", op_name=res.name),
            "number_in_job": PipelineParam(name="number_in_job", op_name=res.name),
            "run_id": PipelineParam(name="run_id", op_name=res.name),
            "run_name": PipelineParam(name="run_name", op_name=res.name),
            "life_cycle_state": PipelineParam(name="life_cycle_state", op_name=res.name),
            "result_state": PipelineParam(name="result_state", op_name=res.name),
            "notebook_output_result": PipelineParam(name="notebook_output_result",
                                                    op_name=res.name),
            "notebook_output_truncated": PipelineParam(name="notebook_output_truncated",
                                                       op_name=res.name),
            "error": PipelineParam(name="error", op_name=res.name),
            "manifest": PipelineParam(name="manifest", op_name=res.name)
        }
        self.assertEqual(res.outputs, expected_outputs)
        self.assertEqual(
            res.output,
            PipelineParam(name="name", op_name=res.name)
        )
        self.assertEqual(res.dependent_names, [])
        self.assertEqual(res.k8s_resource["kind"], "Run")
        self.assertEqual(res.k8s_resource["metadata"]["name"], "test-run")
        self.assertEqual(res.k8s_resource["spec"], expected_spec)

class TestDeleteRunOp(unittest.TestCase):

    def test_databricks_delete_run_without_k8s_or_run_name(self):
        def my_pipeline():
            DeleteRunOp(
                name="deleterun"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_delete_run(self):
        def my_pipeline():

            res = DeleteRunOp(
                name="deleterun",
                run_name="test-run"
            )

            self.assertEqual(res.name, "deleterun")
            self.assertEqual(res.resource.action, "delete")
            self.assertEqual(res.resource.success_condition, None)
            self.assertEqual(res.resource.failure_condition, None)
            self.assertEqual(res.resource.manifest, None)
            self.assertEqual(res.attribute_outputs, {})
            self.assertEqual(res.outputs, {})
            self.assertEqual(res.output, None)
            self.assertEqual(res.dependent_names, [])
            self.assertEqual(res.k8s_resource["kind"], "Run")
            self.assertEqual(res.k8s_resource["metadata"]["name"], "test-run")

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

if __name__ == '__main__':
    unittest.main()
