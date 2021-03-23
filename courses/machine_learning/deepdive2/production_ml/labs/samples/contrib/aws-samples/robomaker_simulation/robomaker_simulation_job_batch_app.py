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

robomaker_sim_job_batch_op = components.load_component_from_file(
    components_dir + "/simulation_job_batch/component.yaml"
)

robomaker_delete_sim_app_op = components.load_component_from_file(
    components_dir + "/delete_simulation_app/component.yaml"
)

simulation_app_name = "robomaker-pipeline-simulation-batch-application"
sources_bucket = "your_sagemaker_bucket_name"
sources_key = "object-tracker/simulation_ws.tar.gz"
sources_architecture = "X86_64"
simulation_software_name = "Gazebo"
simulation_software_version = "7"
robot_software_name = "ROS"
robot_software_version = "Kinetic"
rendering_engine_name = "OGRE"
rendering_engine_version = "1.x"
role = "your_sagemaker_role_name"

job_requests = [
    {
        "outputLocation": {
            "s3Bucket": "kf-pipelines-robomaker-output",
            "s3Prefix": "test-output-key",
        },
        "loggingConfig": {"recordAllRosTopics": True},
        "maxJobDurationInSeconds": 900,
        "iamRole": "your_sagemaker_role_name",
        "failureBehavior": "Fail",
        "simulationApplications": [
            {
                "application": "test-arn",
                "launchConfig": {
                    "packageName": "object_tracker_simulation",
                    "launchFile": "evaluation.launch",
                    "environmentVariables": {
                        "MODEL_S3_BUCKET": "your_sagemaker_bucket_name",
                        "MODEL_S3_PREFIX": "rl-object-tracker-sagemaker-201116-051751",
                        "ROS_AWS_REGION": "us-east-1",
                        "MARKOV_PRESET_FILE": "object_tracker.py",
                        "NUMBER_OF_ROLLOUT_WORKERS": "1",
                    },
                    "streamUI": True,
                },
            }
        ],
        "vpcConfig": {
            "subnets": ["subnet-0efc73526db16a4a4", "subnet-0b8af626f39e7d462",],
            "securityGroups": ["sg-0490601e83f220e82"],
            "assignPublicIp": True,
        },
    }
]


@dsl.pipeline(
    name="RoboMaker Job Batch Pipeline",
    description="RoboMaker simulation job batch is launched via a pipeline component",
)
def robomaker_simulation_job_batch_app_pipeline(
    region="us-east-1",
    role=role,
    name=simulation_app_name
    + "".join(random.choice(string.ascii_lowercase) for i in range(10)),
    sources=[
        {
            "s3Bucket": sources_bucket,
            "s3Key": sources_key,
            "architecture": sources_architecture,
        }
    ],
    simulation_software_name=simulation_software_name,
    simulation_software_version=simulation_software_version,
    robot_software_name=robot_software_name,
    robot_software_version=robot_software_version,
    rendering_engine_name=rendering_engine_name,
    rendering_engine_version=rendering_engine_version,
    timeout_in_secs="900",
    max_concurrency="3",
    simulation_job_requests=job_requests,
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

    robomaker_simulation_batch_job = robomaker_sim_job_batch_op(
        region=region,
        role=role,
        timeout_in_secs=timeout_in_secs,
        max_concurrency=max_concurrency,
        simulation_job_requests=simulation_job_requests,
        sim_app_arn=robomaker_create_sim_app.outputs["arn"],
    ).after(robomaker_create_sim_app)
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))

    robomaker_delete_sim_app = robomaker_delete_sim_app_op(
        region=region, arn=robomaker_create_sim_app.outputs["arn"],
    ).after(robomaker_simulation_batch_job, robomaker_create_sim_app)
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(
        robomaker_simulation_job_batch_app_pipeline, __file__ + ".zip"
    )
