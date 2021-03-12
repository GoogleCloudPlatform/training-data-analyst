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

launch_config = {
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
}

simulation_app_name = "robomaker-pipeline-simulation-application"
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
output_bucket = "kf-pipelines-robomaker-output"
output_key = "test-output-key"
security_groups = ["sg-0490601e83f220e82"]
subnets = [
    "subnet-0efc73526db16a4a4",
    "subnet-0b8af626f39e7d462",
]


@dsl.pipeline(
    name="RoboMaker Simulation Job Pipeline",
    description="RoboMaker simulation job and simulation application created via pipeline components",
)
def robomaker_simulation_job_app_pipeline(
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
    output_bucket=output_bucket,
    output_path=output_key,
    sim_app_launch_config=launch_config,
    vpc_security_group_ids=security_groups,
    vpc_subnets=subnets,
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

    robomaker_simulation_job = robomaker_sim_job_op(
        region=region,
        role=role,
        output_bucket=output_bucket,
        output_path=output_path,
        max_run=300,
        failure_behavior="Fail",
        sim_app_arn=robomaker_create_sim_app.outputs["arn"],
        sim_app_launch_config=sim_app_launch_config,
        vpc_security_group_ids=vpc_security_group_ids,
        vpc_subnets=vpc_subnets,
        use_public_ip="True",
    ).after(robomaker_create_sim_app)
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))

    robomaker_delete_sim_app = robomaker_delete_sim_app_op(
        region=region, arn=robomaker_create_sim_app.outputs["arn"],
    ).after(robomaker_simulation_job, robomaker_create_sim_app)
    # .apply(use_aws_secret('aws-secret', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'))


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(
        robomaker_simulation_job_app_pipeline, __file__ + ".zip"
    )
