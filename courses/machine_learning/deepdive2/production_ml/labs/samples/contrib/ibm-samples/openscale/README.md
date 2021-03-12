# Watson OpenScale Example

This simple OpenScale pipeline will demonstrate how to train a model using IBM Spark Service, store and deploy it with Watson Machine Learning, and then use Watson OpenScale for fairness and quality monitoring.

## Prerequisites
This pipeline requires the user to have provisioned OpenScale, Spark, and Machine Learning Service on Watson, a cloud object store set up and the service credentials configured in the creds.ini file.

To provision your own OpenScale, Spark, Watson Machine Learning services and cloud object store, following are the required steps.

1. IBM Watson Machine Learning service instance

To create a Watson Machine Learning service, go to [IBM Cloud](https://cloud.ibm.com/), login with IBM account id first. From the `Catalog` page, click on `AI` tab on the left side to go to this [page](https://cloud.ibm.com/catalog?category=ai). Then click on the [`Machine Learning`](https://cloud.ibm.com/catalog/services/machine-learning) link and follow the instructions to create the service.

Once the service is created, from the service's `Dashboard`, follow the instructions to generate `service credentials`. Refer to IBM Cloud [documents](https://cloud.ibm.com/docs) for help if needed. Collect the `url`, `apikey`, and `instance_id` info from the service credentials as these will be required to access the service.

2. IBM Watson OpenScale service instance

The IBM Watson OpenScale service will help us monitor the quality and fairness status for the deployed models. From the `Catalog` page, click on `AI` tab on the left side to go to this [page](https://cloud.ibm.com/catalog?category=ai). Then click on the [`Watson OpenScale`](https://cloud.ibm.com/catalog/services/watson-openscale) link and follow the instructions to create the service.

Once the service is created, click on service's `Launch Application` and click on configuration (the 4th icon on the left side) from the new pop up link. Collect the `Datamart ID` which is the GUID for Watson OpenScale.

In addition, collect the IBM Cloud API Key from this [page](https://cloud.ibm.com/iam#/apikeys) to enable service binding for OpenScale service.

3. IBM Spark service instance

The IBM Spark service will provide several spark executors to help train our example model. From the `Catalog` page, click on `Web and Application` tab on the left side to go to this [page](https://cloud.ibm.com/catalog?category=app_services). Then click on the [`Apache Spark`](https://cloud.ibm.com/catalog/services/apache-spark) link and follow the instructions to create the service.

Once the service is created, from the service's `Service credentials` on the left side, follow the instructions to generate `service credentials`. Refer to IBM Cloud [documents](https://cloud.ibm.com/docs) for help if needed.
Collect the `tenant_secret`, `tenant_id`, `cluster_master_url`, and `instance_id` info from the service credentials as these will be required to access the service.

4. A cloud object store

Watson Machine Learning service loads datasets from cloud object store and stores model outputs and other artifacts to cloud object store. Users can use any cloud object store they already preserve. Users can also create a cloud object store with `IBM Cloud Object Storage` service by following this [link](https://console.bluemix.net/catalog/services/cloud-object-storage).

Collect the `endpoint`, `access_key_id` and `secret_access_key` fields from the service credentials for the cloud object store. Create the service credentials first if not exist. To ensure generating HMAC credentials, specify the following in the `Add Inline Configuration Parameters` field: `{"HMAC":true}`.

Create a bucket for storing the train datasets and model source codes.

Then, upload all the files in the `source` folder to the created bucket.

5. Set up access credentials

This pipeline sample reads the credentials from a file hosted in a github repo. Refer to `creds.ini` file and input user's specific credentials. Then upload the file to a github repo the user has access.

To access the credentials file, the user should provide a github access token and the link to the raw content of the file. Modify the `GITHUB_TOKEN` and `CONFIG_FILE_URL` variables in the below code block and run the Python code to create a Kubernetes secret using the KubeFlow pipeline.

```python
import kfp.dsl as dsl
import kfp.components as components
import kfp
secret_name = 'aios-creds'
configuration_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/commons/config/component.yaml')

@dsl.pipeline(
    name='create secret',
    description=''
)
def secret_pipeline(
    GITHUB_TOKEN='',
    CONFIG_FILE_URL='https://raw.githubusercontent.com/user/repository/branch/creds.ini',
):
  get_configuration = configuration_op(
                  token=GITHUB_TOKEN,
                  url=CONFIG_FILE_URL,
                  name=secret_name
  )

kfp.Client().create_run_from_pipeline_func(secret_pipeline, arguments={})
```

## Instructions

First, install the necessary Python Packages
```shell
pip3 install ai_pipeline_params
```

In this repository, run the following commands to create the argo files using the Kubeflow pipeline SDK.
```shell
dsl-compile --py openscale.py --output openscale.tar.gz
```

Then, submit `openscale.tar.gz` to the kubeflow pipeline UI. From there you can create different experiments and runs with the OpenScale pipeline.

## Pipeline Parameters
- **bucket-name**: Object Storage bucket that has Spark training files and OpenScale manifest
- **training-data-link**: Link to a public data source if the data is not being preprocessed.
- **postgres-schema-name**: PostgreSQL schema name for storing model payload metrics
- **label-name**: Model label name in the dataset.
- **problem-type**: Model output type. Possible options are `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION`, and `REGRESSION`
- **threshold**: Model threshold that is recommended for the OpenScale service to monitor.
- **aios-manifest-path**: Manifest files path in the object storage that defines the fairness definition and model schema.
- **model-file-path**: Model file path in the object storage for the spark service to execute.
- **spark-entrypoint**: Entrypoint command to execute the model training using spark service.
- **model-name**: Model name for storing the trained model in Watson Machine Learning service.
- **deployment-name**: Deployment name for deploying the stored model in Watson Machine Learning service.

## Credentials needed to be stored in the creds.ini
- **aios_guid**: GUID of the OpenScale service
- **cloud_api_key**: IBM Cloud API Key
- **postgres_uri**: PostgreSQL URI for storing model payload. Leave it with the empty string `""` if you wish to use the default database that comes with the OpenScale service.
- **spark_tenant_id**: Spark tenant ID from the IBM Apache Spark service.
- **spark_tenant_secret**: Spark tenant secret from the IBM Apache Spark service.
- **spark_cluster_master_url**: Spark cluster master URL from the IBM Apache Spark service.
- **spark_instance_id**: Spark instance ID from the IBM Apache Spark service.
- **cos_endpoint**: Object Storage endpoint.
- **cos_access_key**: Object Storage access key ID
- **cos_secret_key**: Object Storage secret access key.
- **wml_url**: URL endpoint from the Watson Machine Learning service.
- **wml_username**: Username from the Watson Machine Learning service.
- **wml_password**: Password from the Watson Machine Learning service.
- **wml_instance_id**: Instance ID from the Watson Machine Learning service.
- **wml_apikey**: API Key from the Watson Machine Learning service.
