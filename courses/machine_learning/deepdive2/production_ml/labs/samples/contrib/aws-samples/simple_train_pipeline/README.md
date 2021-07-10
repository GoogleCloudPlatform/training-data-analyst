# Simple pipeline for the training component

An example pipeline with only one [training component](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/train).


## Prerequisites 

Make sure you have set up your EKS cluster as described in this [README.md](https://github.com/kubeflow/pipelines/blob/master/samples/contrib/aws-samples/README.md).

Use the following python script to copy `train_data`, `test_data`, and `valid_data.csv` to your bucket.  
[Create a bucket](https://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html) in `us-east-1` region if you don't have one already. 
For the purposes of this demonstration, all resources will be created in the `us-east-1` region.


Create a new file named `s3_sample_data_creator.py` with the following content:
```
import pickle, gzip, numpy, urllib.request, json
from urllib.parse import urlparse

###################################################################
# This is the only thing that you need to change to run this code 
# Give the name of your S3 bucket 
bucket = '<bucket-name>' 

# If you are gonna use the default values of the pipeline then 
# give a bucket name which is in us-east-1 region 
###################################################################


# Load the dataset
urllib.request.urlretrieve("http://deeplearning.net/data/mnist/mnist.pkl.gz", "mnist.pkl.gz")
with gzip.open('mnist.pkl.gz', 'rb') as f:
    train_set, valid_set, test_set = pickle.load(f, encoding='latin1')


# Upload dataset to S3
from sagemaker.amazon.common import write_numpy_to_dense_tensor
import io
import boto3

train_data_key = 'mnist_kmeans_example/train_data'
test_data_key = 'mnist_kmeans_example/test_data'
train_data_location = 's3://{}/{}'.format(bucket, train_data_key)
test_data_location = 's3://{}/{}'.format(bucket, test_data_key)
print('training data will be uploaded to: {}'.format(train_data_location))
print('training data will be uploaded to: {}'.format(test_data_location))

# Convert the training data into the format required by the SageMaker KMeans algorithm
buf = io.BytesIO()
write_numpy_to_dense_tensor(buf, train_set[0], train_set[1])
buf.seek(0)

boto3.resource('s3').Bucket(bucket).Object(train_data_key).upload_fileobj(buf)

# Convert the test data into the format required by the SageMaker KMeans algorithm
write_numpy_to_dense_tensor(buf, test_set[0], test_set[1])
buf.seek(0)

boto3.resource('s3').Bucket(bucket).Object(test_data_key).upload_fileobj(buf)

# Convert the valid data into the format required by the SageMaker KMeans algorithm
numpy.savetxt('valid-data.csv', valid_set[0], delimiter=',', fmt='%g')
s3_client = boto3.client('s3')
input_key = "{}/valid_data.csv".format("mnist_kmeans_example/input")
s3_client.upload_file('valid-data.csv', bucket, input_key)
```
Run this file with the follow command: `python3 s3_sample_data_creator.py`


## Steps 
1. Compile the pipeline:  
   `dsl-compile --py training-pipeline.py --output training-pipeline.tar.gz`
2. In the Kubeflow UI, upload this compiled pipeline specification (the .tar.gz file) and click on create run.
3. Once the pipeline completes, you can see the outputs under 'Output parameters' in the Training component's Input/Output section.

Example inputs to this pipeline :
```buildoutcfg
region : us-east-1
endpoint_url : <leave this empty>
image : 382416733822.dkr.ecr.us-east-1.amazonaws.com/kmeans:1
training_input_mode : File
hyperparameters : {"k": "10", "feature_dim": "784"}
channels : In this JSON, along with other parameters you need to pass the S3 Uri where you have data

                [
                  {
                    "ChannelName": "train",
                    "DataSource": {
                      "S3DataSource": {
                        "S3Uri": "s3://<your_bucket_name>/mnist_kmeans_example/train_data",
                        "S3DataType": "S3Prefix",
                        "S3DataDistributionType": "FullyReplicated"
                      }
                    },
                    "ContentType": "",
                    "CompressionType": "None",
                    "RecordWrapperType": "None",
                    "InputMode": "File"
                  }
                ]

instance_type : ml.m5.2xlarge
instance_count : 1
volume_size : 50
max_run_time : 3600
model_artifact_path : This is where the output model will be stored 
                      s3://<your_bucket_name>/mnist_kmeans_example/output
output_encryption_key : <leave this empty>
network_isolation : True
traffic_encryption : False
spot_instance : False
max_wait_time : 3600
checkpoint_config : {}
role : Paste the role ARN that you noted down  
       (The IAM role with Full SageMaker permissions and S3 access)
       Example role input->  arn:aws:iam::999999999999:role/SageMakerExecutorKFP
```


# Resources
* [Using Amazon built-in algorithms](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-algo-docker-registry-paths.html)
