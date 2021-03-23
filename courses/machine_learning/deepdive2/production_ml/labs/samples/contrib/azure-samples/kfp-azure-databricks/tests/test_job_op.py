import unittest
from pathlib import Path
import kfp
from kfp.dsl import PipelineParam
from databricks import CreateJobOp, DeleteJobOp

class TestCreateJobOp(unittest.TestCase):

    def test_databricks_create_job_without_k8s_or_job_name(self):
        def my_pipeline():
            CreateJobOp(
                name="createjob",
                new_cluster={
                    "spark_version": "5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                libraries=[
                    {
                        "jar": "dbfs:/my-jar.jar"
                    },
                    {
                        "maven": {
                            "coordinates": "org.jsoup:jsoup:1.7.2"
                        }
                    }
                ],
                timeout_seconds=3600,
                max_retries=1,
                schedule={
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles"
                },
                spark_jar_task={
                    "main_class_name": "com.databricks.ComputeModels"
                }
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_create_job_with_new_cluster_and_spark_jar_task(self):
        def my_pipeline():
            job_name = "test-job"
            new_cluster = {
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            }
            libraries = [
                {
                    "jar": "dbfs:/my-jar.jar"
                },
                {
                    "maven": {
                        "coordinates": "org.jsoup:jsoup:1.7.2"
                    }
                }
            ]
            timeout_seconds = 3600
            max_retries = 1
            schedule = {
                "quartz_cron_expression": "0 15 22 ? * *",
                "timezone_id": "America/Los_Angeles"
            }
            spark_jar_task = {
                "main_class_name": "com.databricks.ComputeModels"
            }

            expected_spec = {
                "name": job_name,
                "new_cluster": new_cluster,
                "libraries": libraries,
                "timeout_seconds": timeout_seconds,
                "max_retries": max_retries,
                "schedule": schedule,
                "spark_jar_task": spark_jar_task
            }

            res = CreateJobOp(
                name="createjob",
                job_name=job_name,
                new_cluster=new_cluster,
                libraries=libraries,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                schedule=schedule,
                spark_jar_task=spark_jar_task
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_job_with_new_cluster_and_spark_python_task(self):
        def my_pipeline():
            job_name = "test-job"
            new_cluster = {
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            }
            timeout_seconds = 3600
            max_retries = 3
            min_retry_interval_millis = 3600
            retry_on_timeout = True
            schedule = {
                "quartz_cron_expression": "0 15 22 ? * *",
                "timezone_id": "America/Los_Angeles"
            }
            spark_python_task = {
                "python_file": "dbfs:/docs/pi.py",
                "parameters": [
                    "10"
                ]
            }

            expected_spec = {
                "name": job_name,
                "new_cluster": new_cluster,
                "timeout_seconds": timeout_seconds,
                "max_retries": max_retries,
                "min_retry_interval_millis": min_retry_interval_millis,
                "retry_on_timeout": retry_on_timeout,
                "schedule": schedule,
                "spark_python_task": spark_python_task
            }

            res = CreateJobOp(
                name="createjob",
                job_name=job_name,
                new_cluster=new_cluster,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                min_retry_interval_millis=min_retry_interval_millis,
                retry_on_timeout=retry_on_timeout,
                schedule=schedule,
                spark_python_task=spark_python_task
            )
            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_job_with_new_cluster_and_spark_submit_task(self):
        def my_pipeline():
            job_name = "test-job"
            new_cluster = {
                "spark_version": "5.3.x-scala2.11",
                "node_type_id": "Standard_D3_v2",
                "num_workers": 2
            }
            schedule = {
                "quartz_cron_expression": "0 15 22 ? * *",
                "timezone_id": "America/Los_Angeles"
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
                "name": job_name,
                "new_cluster": new_cluster,
                "schedule": schedule,
                "spark_submit_task": spark_submit_task
            }

            res = CreateJobOp(
                name="createjob",
                job_name=job_name,
                new_cluster=new_cluster,
                schedule=schedule,
                spark_submit_task=spark_submit_task
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_job_with_existing_cluster_and_notebook_task(self):
        def my_pipeline():
            job_name = "test-job"
            existing_cluster_id = "1201-my-cluster"
            schedule = {
                "quartz_cron_expression": "0 15 22 ? * *",
                "timezone_id": "America/Los_Angeles"
            }
            notebook_task = {
                "notebook_path": "/Users/donald@duck.com/my-notebook"
            }
            timeout_seconds = 120

            expected_spec = {
                "name": job_name,
                "existing_cluster_id": existing_cluster_id,
                "schedule": schedule,
                "notebook_task": notebook_task,
                "timeout_seconds": timeout_seconds
            }

            res = CreateJobOp(
                name="createjob",
                job_name=job_name,
                existing_cluster_id=existing_cluster_id,
                schedule=schedule,
                notebook_task=notebook_task,
                timeout_seconds=timeout_seconds
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_job_with_spec(self):
        def my_pipeline():
            spec = {
                "name": "test-job",
                "new_cluster": {
                    "spark_version": "5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "libraries": [
                    {
                        "jar": "dbfs:/my-jar.jar"
                    },
                    {
                        "maven": {
                            "coordinates": "org.jsoup:jsoup:1.7.2"
                        }
                    }
                ],
                "timeout_seconds": 3600,
                "max_retries": 1,
                "schedule": {
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles"
                },
                "spark_jar_task": {
                    "main_class_name": "com.databricks.ComputeModels"
                }
            }

            res = CreateJobOp(
                name="createjob",
                spec=spec
            )

            self.assert_res(res, spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_job_with_spec_and_extra_args(self):
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
                "name": "test-job",
                "new_cluster": {
                    "spark_version":"5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "schedule": {
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles"
                },
                "spark_submit_task": {
                    "parameters": [
                        "--class"
                    ]
                }
            }

            expected_spec = {
                "name": "test-job",
                "new_cluster": {
                    "spark_version": "5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "schedule": {
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles"
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

            res = CreateJobOp(
                name="createjob",
                spec=spec,
                spark_submit_task=spark_submit_task
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_job_with_json_spec(self):
        def my_pipeline():
            job_name = "test-job"
            json_spec = """
            {
                "new_cluster": {
                    "spark_version": "5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "libraries": [
                    {
                        "jar": "dbfs:/my-jar.jar"
                    },
                    {
                        "maven": {
                            "coordinates": "org.jsoup:jsoup:1.7.2"
                        }
                    }
                ],
                "timeout_seconds": 3600,
                "max_retries": 1,
                "schedule": {
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles"
                },
                "spark_jar_task": {
                    "main_class_name": "com.databricks.ComputeModels"
                }
            }
            """

            expected_spec = {
                "name": job_name,
                "new_cluster": {
                    "spark_version": "5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "libraries": [
                    {
                        "jar": "dbfs:/my-jar.jar"
                    },
                    {
                        "maven": {
                            "coordinates": "org.jsoup:jsoup:1.7.2"
                        }
                    }
                ],
                "timeout_seconds": 3600,
                "max_retries": 1,
                "schedule": {
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles"
                },
                "spark_jar_task": {
                    "main_class_name": "com.databricks.ComputeModels"
                }
            }

            res = CreateJobOp.from_json_spec(
                name="createjob",
                job_name=job_name,
                json_spec=json_spec
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def test_databricks_create_job_with_json_file_spec(self):
        def my_pipeline():
            job_name = "test-job"
            current_path = Path(__file__).parent
            json_spec_file_name = current_path.joinpath("job_spec.json")

            expected_spec = {
                "name": job_name,
                "new_cluster": {
                    "spark_version": "5.3.x-scala2.11",
                    "node_type_id": "Standard_D3_v2",
                    "num_workers": 2
                },
                "libraries": [
                    {
                        "jar": "dbfs:/my-jar.jar"
                    },
                    {
                        "maven": {
                            "coordinates": "org.jsoup:jsoup:1.7.2"
                        }
                    }
                ],
                "timeout_seconds": 3600,
                "max_retries": 1,
                "schedule": {
                    "quartz_cron_expression": "0 15 22 ? * *",
                    "timezone_id": "America/Los_Angeles"
                },
                "spark_jar_task": {
                    "main_class_name": "com.databricks.ComputeModels"
                }
            }

            res = CreateJobOp.from_file_name(
                name="createjob",
                job_name=job_name,
                file_name=json_spec_file_name
            )

            self.assert_res(res, expected_spec)

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

    def assert_res(self, res, expected_spec):
        self.assertEqual(res.name, "createjob")
        self.assertEqual(res.resource.action, "create")
        self.assertEqual(
            res.resource.success_condition,
            "status.job_status.job_id > 0"
        )
        self.assertEqual(res.resource.failure_condition, None)
        self.assertEqual(res.resource.manifest, None)
        expected_attribute_outputs = {
            "name": "{.metadata.name}",
            "job_id": "{.status.job_status.job_id}",
            "job_name": "{.status.job_status.settings.name}",
            "manifest": "{}"
        }
        self.assertEqual(res.attribute_outputs, expected_attribute_outputs)
        expected_outputs = {
            "name": PipelineParam(name="name", op_name=res.name),
            "job_id": PipelineParam(name="job_id", op_name=res.name),
            "job_name": PipelineParam(name="job_name", op_name=res.name),
            "manifest": PipelineParam(name="manifest", op_name=res.name)
        }
        self.assertEqual(res.outputs, expected_outputs)
        self.assertEqual(
            res.output,
            PipelineParam(name="name", op_name=res.name)
        )
        self.assertEqual(res.dependent_names, [])
        self.assertEqual(res.k8s_resource["kind"], "Djob")
        self.assertEqual(res.k8s_resource["metadata"]["name"], "test-job")
        self.assertEqual(res.k8s_resource["spec"], expected_spec)

class TestDeleteJobOp(unittest.TestCase):

    def test_databricks_delete_job_without_k8s_or_job_name(self):
        def my_pipeline():
            DeleteJobOp(
                name="deletejob"
            )

        self.assertRaises(ValueError, lambda: kfp.compiler.Compiler()._create_workflow(my_pipeline))

    def test_databricks_delete_job(self):
        def my_pipeline():

            res = DeleteJobOp(
                name="deletejob",
                job_name="test-job"
            )

            self.assertEqual(res.name, "deletejob")
            self.assertEqual(res.resource.action, "delete")
            self.assertEqual(res.resource.success_condition, None)
            self.assertEqual(res.resource.failure_condition, None)
            self.assertEqual(res.resource.manifest, None)
            self.assertEqual(res.attribute_outputs, {})
            self.assertEqual(res.outputs, {})
            self.assertEqual(res.output, None)
            self.assertEqual(res.dependent_names, [])
            self.assertEqual(res.k8s_resource["kind"], "Djob")
            self.assertEqual(res.k8s_resource["metadata"]["name"], "test-job")

        kfp.compiler.Compiler()._create_workflow(my_pipeline)

if __name__ == '__main__':
    unittest.main()
