#!/usr/bin/env python3

# Uncomment the apply(use_aws_secret()) below if you are not using OIDC
# more info : https://github.com/kubeflow/pipelines/tree/master/samples/contrib/aws-samples/README.md

import kfp
import os
from kfp import components
from kfp import dsl
from kfp.aws import use_aws_secret
from sagemaker.rl import RLEstimator, RLToolkit


cur_file_dir = os.path.dirname(__file__)
components_dir = os.path.join(cur_file_dir, "../../../../components/aws/sagemaker/")

sagemaker_rlestimator_op = components.load_component_from_file(
    components_dir + "/rlestimator/component.yaml"
)

output_bucket_name = "kf-pipelines-rlestimator-output"
input_bucket_name = "kf-pipelines-rlestimator-input"
input_key = "sourcedir.tar.gz"
job_name_prefix = "rlestimator-pipeline-custom-image"
image_uri = "your_sagemaker_image_name"
role = "your_sagemaker_role_name"
security_groups = ["sg-0490601e83f220e82"]
subnets = [
    "subnet-0efc73526db16a4a4",
    "subnet-0b8af626f39e7d462",
]

# You need to specify your own metric_definitions if using a custom image_uri
metric_definitions = RLEstimator.default_metric_definitions(RLToolkit.RAY)


@dsl.pipeline(
    name="RLEstimator Custom Docker Image",
    description="RLEstimator training job where we provide a reference to a Docker image containing our training code",
)
def rlestimator_training_custom_pipeline(
    region="us-east-1",
    entry_point="train-unity.py",
    source_dir="s3://{}/{}".format(input_bucket_name, input_key),
    image_uri=image_uri,
    assume_role=role,
    instance_type="ml.c5.2xlarge",
    instance_count=1,
    output_path="s3://{}/".format(output_bucket_name),
    base_job_name=job_name_prefix,
    metric_definitions=metric_definitions,
    hyperparameters={},
    vpc_security_group_ids=security_groups,
    vpc_subnets=subnets,
):
    rlestimator_training_custom = sagemaker_rlestimator_op(
        region=region,
        entry_point=entry_point,
        source_dir=source_dir,
        image=image_uri,
        role=assume_role,
        model_artifact_path=output_path,
        job_name=base_job_name,
        metric_definitions=metric_definitions,
        instance_type=instance_type,
        instance_count=instance_count,
        hyperparameters=hyperparameters,
        vpc_security_group_ids=vpc_security_group_ids,
        vpc_subnets=vpc_subnets,
    )  # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(
        rlestimator_training_custom_pipeline, __file__ + ".zip"
    )
