# MNIST Classification with KMeans

The `mnist-classification-pipeline.py` sample runs a pipeline to train a classficiation model using Kmeans with MNIST dataset on SageMaker. This example was taken from an existing [SageMaker example](https://github.com/awslabs/amazon-sagemaker-examples/blob/master/sagemaker-python-sdk/1P_kmeans_highlevel/kmeans_mnist.ipynb) and modified to work with the Amazon SageMaker Components for Kubeflow Pipelines.

## Prerequisites 

### Setup K8s cluster and authentication
Make sure you have the setup explained in this [README.md](https://github.com/kubeflow/pipelines/blob/master/samples/contrib/aws-samples/README.md)

### Sample MNIST dataset

The following commands will copy the data extraction pre-processing script to an S3 bucket which we will use to store artifacts for the pipeline.

1. [Create a bucket](https://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html) in `us-east-1` region if you don't have one already. 
For the purposes of this demonstration, all resources will be created in the us-east-1 region.

2. Upload the `mnist-kmeans-sagemaker/kmeans_preprocessing.py` file to your bucket with the prefix `mnist_kmeans_example/processing_code/kmeans_preprocessing.py`.
This can be done with the following command, replacing `<bucket-name>` with the name of the bucket you previously created in `us-east-1`:
    ```
    aws s3 cp mnist-kmeans-sagemaker/kmeans_preprocessing.py s3://<bucket-name>/mnist_kmeans_example/processing_code/kmeans_preprocessing.py
    ```

## Compiling the pipeline template

Follow the guide to [building a pipeline](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/) to install the Kubeflow Pipelines SDK, then run the following command to compile the sample Python into a workflow specification. The specification takes the form of a YAML file compressed into a `.tar.gz` file.

```bash
dsl-compile --py mnist-classification-pipeline.py --output mnist-classification-pipeline.tar.gz
```


## Deploying the pipeline

Open the Kubeflow pipelines UI. Create a new pipeline, and then upload the compiled specification (`.tar.gz` file) as a new pipeline template.

Provide the `role_arn` and `bucket_name` you created as pipeline inputs.

Once the pipeline done, you can go to `batch_transform_ouput` to check your batch prediction results.
You will also have an model endpoint in service. Refer to [Prediction section](#Prediction) below to run predictions aganist your deployed model aganist the endpoint. Please remember to clean up the endpoint.


## Prediction

1. Find your endpoint name either by,
  - Opening SageMaker [console](https://us-east-1.console.aws.amazon.com/sagemaker/home?region=us-east-1#/endpoints),  or
  - Clicking the `sagemaker-deploy-model-endpoint_name` under `Output artifacts` of `SageMaker - Deploy Model` component of the pipeline run

2. Setup AWS credentials with `sagemaker:InvokeEndpoint` access. [Sample commands](https://sagemaker.readthedocs.io/en/stable/workflows/kubernetes/using_amazon_sagemaker_components.html#configure-permissions-to-run-predictions)
3. Update the `ENDPOINT_NAME` variable in the script below
4. Run the script below to invoke the endpoint

```python
import json
import io
import boto3
import pickle
import urllib.request
import gzip
import numpy

ENDPOINT_NAME="<your_endpoint_name>"

# Simple function to create a csv from numpy array
def np2csv(arr):
    csv = io.BytesIO()
    numpy.savetxt(csv, arr, delimiter=',', fmt='%g')
    return csv.getvalue().decode().rstrip()

# Prepare input for the model
urllib.request.urlretrieve("http://deeplearning.net/data/mnist/mnist.pkl.gz", "mnist.pkl.gz")
with gzip.open('mnist.pkl.gz', 'rb') as f:
    train_set, _, _ = pickle.load(f, encoding='latin1')

payload = np2csv(train_set[0][30:31])

# Run prediction aganist the endpoint created by the pipeline
runtime = boto3.Session(region_name='us-east-1').client('sagemaker-runtime')
response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                   ContentType='text/csv',
                                   Body=payload)
result = json.loads(response['Body'].read().decode())
print(result)
```

## Components source

Hyperparameter Tuning:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/hyperparameter_tuning/src)

Training:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/train/src)

Model creation:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/model/src)

Endpoint Deployment:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/deploy/src)

Batch Transformation:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/batch_transform/src)
