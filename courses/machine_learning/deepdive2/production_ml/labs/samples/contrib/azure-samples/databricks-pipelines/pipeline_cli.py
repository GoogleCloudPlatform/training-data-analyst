import os
import sys
import logging
import kfp
import fire

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

class MyCLI:
    """
    CLI for Kubeflow Pipelines.

    This CLI allows us to compile and run our pipelines in Kubeflow Pipelines without accessing
    Kubeflow portal.
    """

    @staticmethod
    def compile(
            path
    ):
        """
        Compile a Kubeflow pipeline.

        Args:
            path: Path to the pipeline (e.g. databricks_run_pipeline.py)
        """

        logging.info("Compiling '%s'...", path)
        compiled_path = f"{path}.tar.gz"
        result = os.system(f"dsl-compile --py {path} --output {compiled_path}")
        if result != 0:
            logging.error("Failed to compile '%s' with error code %i.", path, result)
            sys.exit(result)

        return compiled_path

    @staticmethod
    def run(
            path,
            host,
            params={}
    ):
        """
        Run a compiled pipeline in Kubeflow.

        Args:
            path: Path to the compiled pipeline (e.g. databricks_run_pipeline.py.tar.gz)
            host: Host name to use to talk to Kubeflow Pipelines (e.g. http://localhost:8080/pipeline)
            params: Pipeline parameters (e.g. '{\"run_name\":\"test-run\",\"parameter\":\"10\"}')
        """

        logging.info("Running '%s' in '%s'...", path, host)
        client = kfp.Client(f"{host}")
        try:
            result = client.create_run_from_pipeline_package(
                pipeline_file=path,
                arguments=params
            )
            logging.info("View run: %s/#/runs/details/%s",
                         host,
                         result.run_id)
        except Exception as ex:
            logging.error("Failed to run '{%s}' with error:\n{%s}", path, ex)
            sys.exit(1)

    @staticmethod
    def compile_run(
            path,
            host,
            params={}
    ):
        """
        Compile and run a Kubeflow pipeline.

        Args:
            path: Path to the pipeline (e.g. databricks_run_pipeline.py)
            host: Host name to use to talk to Kubeflow Pipelines (e.g. http://localhost:8080/pipeline)
            params: Pipeline parameters (e.g. '{\"run_name\":\"test-run\",\"parameter\":\"10\"}')
        """

        compiled_path = MyCLI.compile(path)
        MyCLI.run(compiled_path, host, params)

if __name__ == '__main__':
    fire.Fire(MyCLI())
