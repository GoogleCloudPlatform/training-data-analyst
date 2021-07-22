The `mini-image-classification-pipeline.py` sample runs a pipeline to demonstrate usage for the create workteam, Ground Truth, and train components.

This sample is based on [this example](https://github.com/awslabs/amazon-sagemaker-examples/blob/master/ground_truth_labeling_jobs/from_unlabeled_data_to_deployed_machine_learning_model_ground_truth_demo_image_classification/from_unlabeled_data_to_deployed_machine_learning_model_ground_truth_demo_image_classification.ipynb).

The sample goes through the workflow of creating a private workteam, creating data labeling jobs for that team, and running a training job using the new labeled data.

## Prerequisites 

Make sure you have the setup explained in this [README.md](https://github.com/kubeflow/pipelines/blob/master/samples/contrib/aws-samples/README.md)
(This pipeline does not use mnist dataset. Follow the instruction bellow to get sample dataset)

## Prep the dataset, label categories, and UI template

For this demo, you will be using a very small subset of the [Google Open Images dataset](https://storage.googleapis.com/openimages/web/index.html).

Run the following to download `openimgs-annotations.csv`:
```bash
wget --no-verbose https://storage.googleapis.com/openimages/2018_04/test/test-annotations-human-imagelabels-boxable.csv -O openimgs-annotations.csv
```
Create a s3 bucket and run [this python script](https://github.com/kubeflow/pipelines/tree/master/samples/contrib/aws-samples/ground_truth_pipeline_demo/prep_inputs.py) to get the images and generate `train.manifest`, `validation.manifest`, `class_labels.json`, and `instuctions.template`.


## Amazon Cognito user groups

From Cognito note down Pool ID, User Group Name and client ID  
You need this information to fill arguments user_pool, user_groups and client_ID

[Official doc for Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-getting-started.html)

For this demo you can create a new user pool (if you don't have one already).   

AWS console -> Amazon SageMaker -> Ground Truth, Labeling workforces -> Private -> Create Private Team -> Give it "KFP-ground-truth-demo-pool" name and use your email address -> Create Private team -> Click on the radio button and from summary note down the "Amazon Cognito user pool", "App client" and "Labeling portal sign-in URL" -> click on the team name that you created and note down "Amazon Cognito user group"

Use the info that you noted down to fill arguments for the pipeline  
user_pool = Amazon Cognito user pool  
user_groups = Amazon Cognito user group  
client_ID = App client  

> Note : Once you start a run on the pipeline you will receive the ground_truth labeling jobs at "Labeling portal sign-in URL" link 


## Compiling the pipeline template

Follow the guide to [building a pipeline](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/) to install the Kubeflow Pipelines SDK, then run the following command to compile the sample Python into a workflow specification. The specification takes the form of a YAML file compressed into a `.tar.gz` file.


```bash
dsl-compile --py mini-image-classification-pipeline.py --output mini-image-classification-pipeline.tar.gz
```

## Deploying the pipeline

Open the Kubeflow pipelines UI. Create a new pipeline, and then upload the compiled specification (`.tar.gz` file) as a new pipeline template.

The pipeline requires several arguments - replace `role_arn`, Amazon Cognito information, and the S3 input paths with your settings, and run the pipeline.

> Note : team_name, ground_truth_train_job_name and ground_truth_validation_job_name need to be unique or else pipeline will error out if the names already exist

If you are a new worker, you will receive an email with a link to the labeling portal and login information after the create workteam component completes.
During the execution of the two Ground Truth components (one for training data, one for validation data), the labeling jobs will appear in the portal and you will need to complete these jobs.  

After the pipeline finished, you may delete the user pool/ user group and the S3 bucket.

  

## Components source

Create Workteam:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/workteam/src)

Ground Truth Labeling:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/ground_truth/src)

Training:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/train/src)
