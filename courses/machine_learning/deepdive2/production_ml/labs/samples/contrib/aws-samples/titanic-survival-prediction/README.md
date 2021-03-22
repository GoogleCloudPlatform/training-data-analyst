The `titanic-survival-prediction.py` sample runs a Spark ML pipeline to train a classfication model using random forest on AWS Elastic Map Reduce(EMR).

## The dataset

Check Kaggle [Titanic: Machine Learning from Disaster](https://www.kaggle.com/c/titanic) for more details about this problem. 70% training dataset is used to train model and rest 30% for validation.

Please upload training dataset [train.csv](https://www.kaggle.com/c/titanic/data) to your s3 bucket.

## Spark ML Job

Please check [aws-emr-titanic-ml-example](https://github.com/Jeffwan/aws-emr-titanic-ml-example) for example spark project.

To get jar file, you can clone that project and run

```
sbt clean package

# copy this jar to your s3 bucket. main class is `com.amazonaws.emr.titanic.Titanic`
ls target/scala-2.11/titanic-survivors-prediction_2.11-1.0.jar
```

## EMR permission

This pipeline use aws-secret to get access to EMR services, please make sure you have a `aws-secret` in the kubeflow namespace and attach `AmazonElasticMapReduceFullAccess` policy.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aws-secret
  namespace: kubeflow
type: Opaque
data:
  AWS_ACCESS_KEY_ID: YOUR_BASE64_ACCESS_KEY
  AWS_SECRET_ACCESS_KEY: YOUR_BASE64_SECRET_ACCESS
```

> Note: To get base64 string, try `echo -n $AWS_ACCESS_KEY_ID | base64`


## Compiling the pipeline template

Follow the guide to [building a pipeline](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/) to install the Kubeflow Pipelines SDK, then run the following command to compile the sample Python into a workflow specification. The specification takes the form of a YAML file compressed into a `.tar.gz` file.

```bash
dsl-compile --py titanic-survival-prediction.py --output titanic-survival-prediction.tar.gz
```

## Deploying the pipeline

Open the Kubeflow pipelines UI. Create a new pipeline, and then upload the compiled specification (`.tar.gz` file) as a new pipeline template.

Once the pipeline done, you can go to the S3 path specified in `output` to check your prediction results. There're three columes, `PassengerId`, `prediction`, `Survived` (Ground True value)

```
...
4,1,1
5,0,0
6,0,0
7,0,0
...
```

## Components source

Create Cluster:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/emr/create_cluster/src)

Submit Spark Job:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/emr/submit_spark_job/src)

Delete Cluster:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/emr/delete_cluster/src)
