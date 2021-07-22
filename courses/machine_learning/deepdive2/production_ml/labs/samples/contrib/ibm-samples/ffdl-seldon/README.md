# Simple IBM OSS demo

This simple IBM OSS demo will demonstrate how to train a model using [Fabric for Deep Learning](https://github.com/IBM/FfDL) and then deploy it with [Seldon](https://github.com/SeldonIO/seldon-core).

## Prerequisites
1. Install [Fabric for Deep Learning](https://github.com/IBM/FfDL) and [Seldon](https://github.com/SeldonIO/seldon-core) on the same Kubernetes cluster as KubeFlow Pipeline.
2. Create two S3 Object Storage buckets, then store the training data, model definition file, and FfDL manifest file in the training bucket.
  * The training data for this demo is from the [UTKface's aligned & cropped faces dataset](https://susanqq.github.io/UTKFace/). We will be using the data binary `UTKFace.tar.gz`.

  * The model definition file needs to be packaged as `gender-classification.zip`.
    with the following commands
    ```shell
    zip -j source/gender-classification source/model-source-code/gender_classification.py
    ```
    Then upload the model definition file and FfDL manifest file in the source directory. They are named `gender-classification.zip` and `manifest.yml`.

3. Fill in the necessary credentials at [credentials/creds.ini](credentials/creds.ini) and upload it to one of your GitHub private repositories. The details of each parameter are defined below.

## Instructions

### 1. With Command line
First, install the necessary Python Packages
```shell
pip3 install ai_pipeline_params
```

In this repository, run the following commands to create the argo files using the Kubeflow pipeline SDK.
```shell
dsl-compile --py ffdl_pipeline.py --output ffdl-pipeline.tar.gz
```

Then, submit `ffdl-pipeline.tar.gz` to the kubeflow pipeline UI. From there you can create different experiments and runs using the ffdl pipeline definition.

### 2. With Jupyter Notebook
Run `jupyter notebook` to start running your jupyter server and load the notebook `ffdl_pipeline.ipynb` and follow the instructions.


## Pipeline Parameters
- **config-file-url**: GitHub raw content link to the pipeline credentials file
- **github-token**: GitHub Token that can access your private repository
- **model-def-file-path**: Model definition path in the training bucket
- **manifest-file-path**: FfDL manifest path in the training bucket
- **model-deployment-name**: Seldon Model deployment name
- **model-class-name**: PyTorch model class name
- **model-class-file**: Model file that contains the PyTorch model class

## Credentials needed to be stored in GitHub
- **s3_url**: S3 Object storage endpoint for your FfDL training job.
- **s3_access_key_id**: S3 Object storage access key id
- **s3_secret_access_key**: S3 Object storage secret access key
- **training_bucket**: S3 Bucket for the training job data location.
- **result_bucket**: S3 Bucket for the training job result location.
- **ffdl_rest**: RESTAPI endpoint for FfDL.
- **k8s_public_nodeport_ip**: IP of the host machine. It will be used to generate a web service endpoint for the served model.

## Naming convention for Training Model Files

Since libraries such as Spark and OpenCV are huge to put inside the serving containers, users who use libraries which are not from the standard PyTorch container from FfDL should consider defining their PyTorch model class file in a separate Python file. This is because when python tries to load the model class from users' training files, python interpreter will need to read and import all the
modules in memory within the same file in order to properly construct the module dependencies.

Therefore, by default users should consider naming their model class as `ModelClass` and put the model class code in a file call `model_class.py`. However, users can choose not to follow the naming convention as long as they provide the model class and file name as part of the pipeline parameters.
