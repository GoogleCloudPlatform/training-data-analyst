#!/usr/bin/env python3

# Uncomment the apply(use_aws_secret()) below if you are not using OIDC
# more info : https://github.com/kubeflow/pipelines/tree/master/samples/contrib/aws-samples/README.md

import kfp
import os
from kfp import components
from kfp import dsl
from kfp.aws import use_aws_secret


cur_file_dir = os.path.dirname(__file__)
components_dir = os.path.join(cur_file_dir, "../../../../components/aws/sagemaker/")

sagemaker_rlestimator_op = components.load_component_from_file(
    components_dir + "/rlestimator/component.yaml"
)

metric_definitions = [
    {
        "Name": "episode_reward_mean",
        "Regex": "episode_reward_mean: ([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)",
    },
    {
        "Name": "episode_reward_max",
        "Regex": "episode_reward_max: ([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)",
    },
    {
        "Name": "episode_len_mean",
        "Regex": "episode_len_mean: ([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)",
    },
    {"Name": "entropy", "Regex": "entropy: ([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)"},
    {
        "Name": "episode_reward_min",
        "Regex": "episode_reward_min: ([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)",
    },
    {"Name": "vf_loss", "Regex": "vf_loss: ([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)"},
    {
        "Name": "policy_loss",
        "Regex": "policy_loss: ([-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?)",
    },
]

output_bucket_name = "your_sagemaker_bucket_name"
input_bucket_name = "your_sagemaker_bucket_name"
input_key = "rl-newsvendor-2020-11-11-10-43-30-556/source/sourcedir.tar.gz"
job_name_prefix = "rlestimator-pipeline-toolkit-image"
role = "your_sagemaker_role_name"


@dsl.pipeline(
    name="RLEstimator Toolkit & Framework Pipeline",
    description="RLEstimator training job where the AWS Docker image is auto-selected based on the Toolkit and Framework we define",
)
def rlestimator_training_toolkit_pipeline(
    region="us-east-1",
    entry_point="train_news_vendor.py",
    source_dir="s3://{}/{}".format(input_bucket_name, input_key),
    toolkit="ray",
    toolkit_version="0.8.5",
    framework="tensorflow",
    assume_role=role,
    instance_type="ml.c5.2xlarge",
    instance_count=1,
    output_path="s3://{}/".format(output_bucket_name),
    base_job_name=job_name_prefix,
    metric_definitions=metric_definitions,
    max_run=300,
    hyperparameters={},
):
    rlestimator_training_toolkit = sagemaker_rlestimator_op(
        region=region,
        entry_point=entry_point,
        source_dir=source_dir,
        toolkit=toolkit,
        toolkit_version=toolkit_version,
        framework=framework,
        role=assume_role,
        instance_type=instance_type,
        instance_count=instance_count,
        model_artifact_path=output_path,
        job_name=base_job_name,
        metric_definitions=metric_definitions,
        max_run=max_run,
        hyperparameters=hyperparameters,
    )  # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(
        rlestimator_training_toolkit_pipeline, __file__ + ".zip"
    )
