from setuptools import setup
import databricks

setup(
    name='kfp-azure-databricks',
    version=databricks.__version__,
    description='Python package to manage Azure Databricks on Kubeflow Pipelines using Azure Databricks operator for Kubernetes',
    url='https://github.com/kubeflow/pipelines/tree/master/samples/contrib/azure-samples/kfp-azure-databricks',
    packages=['databricks']
)
