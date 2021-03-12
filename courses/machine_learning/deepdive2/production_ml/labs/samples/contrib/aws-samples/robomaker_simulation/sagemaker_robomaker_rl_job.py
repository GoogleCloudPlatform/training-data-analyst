#!/usr/bin/env python3

# Uncomment the apply(use_aws_secret()) below if you are not using OIDC
# more info : https://github.com/kubeflow/pipelines/tree/master/samples/contrib/aws-samples/README.md

import kfp
import os
from kfp import components
from kfp import dsl
import random
import string
from kfp.aws import use_aws_secret

cur_file_dir = os.path.dirname(__file__)
components_dir = os.path.join(cur_file_dir, "../../../../components/aws/sagemaker/")

robomaker_create_sim_app_op = components.load_component_from_file(
    components_dir + "/create_simulation_app/component.yaml"
)

robomaker_sim_job_op = components.load_component_from_file(
    components_dir + "/simulation_job/component.yaml"
)

robomaker_delete_sim_app_op = components.load_component_from_file(
    components_dir + "/delete_simulation_app/component.yaml"
)

sagemaker_rlestimator_op = components.load_component_from_file(
    components_dir + "/rlestimator/component.yaml"
)

metric_definitions = [
    {"Name": "reward-training", "Regex": "^Training>.*Total reward=(.*?),"},
    {"Name": "ppo-surrogate-loss", "Regex": "^Policy training>.*Surrogate loss=(.*?),"},
    {"Name": "ppo-entropy", "Regex": "^Policy training>.*Entropy=(.*?),"},
    {"Name": "reward-testing", "Regex": "^Testing>.*Total reward=(.*?),"},
]

# Simulation Application Inputs
region = "us-east-1"
simulation_software_name = "Gazebo"
simulation_software_version = "7"
robot_software_name = "ROS"
robot_software_version = "Kinetic"
rendering_engine_name = "OGRE"
rendering_engine_version = "1.x"
simulation_app_name = "robomaker-pipeline-objecttracker-sim-app" + "".join(
    random.choice(string.ascii_lowercase) for i in range(10)
)
sources_bucket = "your_sagemaker_bucket_name"
sources_key = "object-tracker/simulation_ws.tar.gz"
sources_architecture = "X86_64"
sources = [
    {
        "s3Bucket": sources_bucket,
        "s3Key": sources_key,
        "architecture": sources_architecture,
    }
]

# RLEstimator Inputs
entry_point = "training_worker.py"
rl_sources_key = "rl-object-tracker-sagemaker-201123-042019/source/sourcedir.tar.gz"
source_dir = "s3://{}/{}".format(sources_bucket, rl_sources_key)
rl_output_path = "s3://{}/".format(sources_bucket)
train_instance_type = "ml.c5.2xlarge"
train_instance_count = 1
toolkit = "coach"
toolkit_version = "0.11"
framework = "tensorflow"
job_name = "rl-kf-pipeline-objecttracker" + "".join(
    random.choice(string.ascii_lowercase) for i in range(10)
)
max_run = 300
s3_prefix = "rl-object-tracker-sagemaker-201123-042019"
hyperparameters = {
    "s3_bucket": sources_bucket,
    "s3_prefix": s3_prefix,
    "aws_region": "us-east-1",
    "RLCOACH_PRESET": "object_tracker",
}
role = "your_sagemaker_role_name"
security_groups = ["sg-0490601e83f220e82"]
subnets = [
    "subnet-0efc73526db16a4a4",
    "subnet-0b8af626f39e7d462",
]

# Simulation Job Inputs
output_bucket = "kf-pipelines-robomaker-output"
output_key = "test-output-key"


@dsl.pipeline(
    name="SageMaker & RoboMaker pipeline",
    description="SageMaker & RoboMaker Reinforcement Learning job where the jobs work together to train an RL model",
)
def sagemaker_robomaker_rl_job(
    region=region,
    role=role,
    name=simulation_app_name,
    sources=sources,
    simulation_software_name=simulation_software_name,
    simulation_software_version=simulation_software_version,
    robot_software_name=robot_software_name,
    robot_software_version=robot_software_version,
    rendering_engine_name=rendering_engine_name,
    rendering_engine_version=rendering_engine_version,
    output_bucket=output_bucket,
    robomaker_output_path=output_key,
    vpc_security_group_ids=security_groups,
    vpc_subnets=subnets,
    entry_point=entry_point,
    source_dir=source_dir,
    toolkit=toolkit,
    toolkit_version=toolkit_version,
    framework=framework,
    assume_role=role,
    instance_type=train_instance_type,
    instance_count=train_instance_count,
    output_path=rl_output_path,
    job_name=job_name,
    metric_definitions=metric_definitions,
    max_run=max_run,
    hyperparameters=hyperparameters,
    sources_bucket=sources_bucket,
    s3_prefix=s3_prefix,
):
    robomaker_create_sim_app = robomaker_create_sim_app_op(
        region=region,
        app_name=name,
        sources=sources,
        simulation_software_name=simulation_software_name,
        simulation_software_version=simulation_software_version,
        robot_software_name=robot_software_name,
        robot_software_version=robot_software_version,
        rendering_engine_name=rendering_engine_name,
        rendering_engine_version=rendering_engine_version,
    )
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))

    rlestimator_training_toolkit_coach = sagemaker_rlestimator_op(
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
        job_name=job_name,
        max_run=max_run,
        hyperparameters=hyperparameters,
        metric_definitions=metric_definitions,
        vpc_subnets=vpc_subnets,
        vpc_security_group_ids=vpc_security_group_ids,
    )
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))

    robomaker_simulation_job = robomaker_sim_job_op(
        region=region,
        role=role,
        output_bucket=output_bucket,
        output_path=robomaker_output_path,
        max_run=3800,
        failure_behavior="Continue",
        sim_app_arn=robomaker_create_sim_app.outputs["arn"],
        sim_app_launch_config={
            "packageName": "object_tracker_simulation",
            "launchFile": "evaluation.launch",
            "environmentVariables": {
                "MODEL_S3_BUCKET": sources_bucket,
                "MODEL_S3_PREFIX": s3_prefix,
                "ROS_AWS_REGION": region,
                "NUMBER_OF_ROLLOUT_WORKERS": "1",
                "MARKOV_PRESET_FILE": "object_tracker.py",
            },
            "streamUI": True,
        },
        vpc_security_group_ids=vpc_security_group_ids,
        vpc_subnets=vpc_subnets,
        use_public_ip="True",
    )
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))

    robomaker_delete_sim_app = robomaker_delete_sim_app_op(
        region=region, arn=robomaker_create_sim_app.outputs["arn"],
    ).after(robomaker_simulation_job, robomaker_create_sim_app)
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(sagemaker_robomaker_rl_job, __file__ + ".zip")
