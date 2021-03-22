The two examples in this directory each run a different type of RLEstimator Reinforcement Learning job as a SageMaker training job.

## Examples

Each example is based on a notebook from the [AWS SageMaker Examples](https://github.com/aws/amazon-sagemaker-examples) repo.
(It should be noted that all of these examples are available by default on all SageMaker Notebook Instance's)

The `rlestimator_pipeline_custom_image` pipeline example is based on the 
[`rl_unity_ray`](https://github.com/aws/amazon-sagemaker-examples/blob/master/reinforcement_learning/rl_unity_ray/rl_unity_ray.ipynb) notebook.

The `rlestimator_pipeline_toolkit_image` pipeline example is based on the
[`rl_news_vendor_ray_custom`](https://github.com/aws/amazon-sagemaker-examples/blob/master/reinforcement_learning/rl_resource_allocation_ray_customEnv/rl_news_vendor_ray_custom.ipynb) notebook.

## Prerequisites

To run these examples you will need to create a number of resources that will then be used as inputs for the pipeline component.

rlestimator_pipeline_custom_image required inputs:
```
output_bucket_name = <bucket used for outputs from the training job>
input_bucket_name = <bucket used for inputs, in this case custom code via a tar.gz>
input_key = <the path and file name of the source code tar.gz>
job_name_prefix = <not required, but can be useful to identify these training jobs>
image_uri = <docker image uri, can be docker.io if you have internet access, but might be easier to use ECR>
assume_role = <sagemaker execution role, this is created for you automatically when you launch a notebook instance>
```

rl_news_vendor_ray_custom required inputs:
```
output_bucket_name = <bucket used for outputs from the training job>
input_bucket_name = <bucket used for inputs, in this case custom code via a tar.gz>
input_key = <the path and file name of the source code tar.gz>
job_name_prefix = <not required, but can be useful to identify these training jobs>
role = <sagemaker execution role, this is created for you automatically when you launch a notebook instance>
```

You could go to the bother of creating all of these resources individually, but it might be easier to run each of the notebooks 
mentioned above, and then use the resources that are created by the notebooks. For the input bucket and output bucket they
will be created under a name like 'sagemaker-us-east-1-520713654638' depending on your region and account number. Within 
these buckets a key will be created for each of your training job runs. After you have executed all cells in each of the notebooks
a key for each training job that has completed will be made and any custom code required for the training job will be placed
there as a .tar.gz file. The tar.gz file full S3 URI can be used as the source_dir input for these pipeline components.


## Compiling the pipeline template

Follow the guide to [building a pipeline](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/) to install the Kubeflow Pipelines SDK, then run the following command to compile the sample Python into a workflow specification. The specification takes the form of a YAML file compressed into a `.tar.gz` file.

```bash
dsl-compile --py rlestimator_pipeline_custom_image.py --output rlestimator_pipeline_custom_image.tar.gz
dsl-compile --py rlestimator_pipeline_toolkit_image.py --output rlestimator_pipeline_toolkit_image.tar.gz
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

RLEstimator Training Job:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/rlestimator/src)
