Examples for creating a simulation application, running a simulation job, running a simulation job batch, and deleting a simulation application.

## Examples

The examples are based on a notebook from the [AWS SageMaker Examples](https://github.com/aws/amazon-sagemaker-examples) repo.

The simulation jobs that are launched by these examples are based on the 
[`rl_objecttracker_robomaker_coach_gazebo`](https://github.com/aws/amazon-sagemaker-examples/tree/3de42334720a7197ea1f15395b66c44cf5ef7fd4/reinforcement_learning/rl_objecttracker_robomaker_coach_gazebo) notebook.
This is an older notebook example, but you can still download it from github and upload directly to Jupyter Lab in SageMaker.


## Prerequisites

To run these examples you will need to create a number of resources that will then be used as inputs for the pipeline component.
Some of the inputs are used to create the RoboMaker Simulation Application and some are used as inputs for the RoboMaker
Simulation Job.

required inputs for simulation job example:
```
role = <robomaker execution role, this is created for you automatically when you launch a notebook instance>
region = <region in which to deploy the robomaker resources>
app_name = <name to be given to the simulation application>
sources = <source code files for the simulation application>
simulation_software_suite = <select the simulation application software suite to use>
robot_software_suite = <select the simulation application robot software suite to use>
rendering_engine = <select the simulation application rendering engine suite to use>
output_bucket = <bucket used for outputs from the training job>
output_path = <key within the output bucket to use for output artifacts>
max_run = <the maximum time to run the simulation job for>
max_run = <the maximum time to run the simulation job for>
failure_behavior = <"Fail" or "Continue">
sim_app_arn = <used as input to simulation job component, comes as an output from simulation application component>
sim_app_launch_config = <dictionary containing launch configurations>
vpc_subnets = <subnets to launch the simulation job into>
vpc_security_group_ids = <security groups to use if launching in a VPC>
use_public_ip = <whether or not to use a public ip to access the simulation job>
```

required inputs for simulation job batch example:
```
role = <robomaker execution role, this is created for you automatically when you launch a notebook instance>
region = <region in which to deploy the robomaker resources>
app_name = <name to be given to the simulation application>
sources = <source code files for the simulation application>
simulation_software_suite = <select the simulation application software suite to use>
robot_software_suite = <select the simulation application robot software suite to use>
rendering_engine = <select the simulation application rendering engine suite to use>
timeout_in_secs = <maximum timeout to wait for simulation jobs in batch to launch>,
max_concurrency = <maximum concurrency for simulation jobs in batch>,
simulation_job_requests = <the definitions for the simulation jobs, things like launch configs and vpc configs are placed in here>,
sim_app_arn=robomaker_create_sim_app.outputs["arn"]
sim_app_arn = <used as input to simulation job component, comes as an output from simulation application component>
```

You could go to the bother of creating all of these resources individually, but it might be easier to run the notebook
mentioned above, and then use the resources that are created by that notebook. The notebook should create the output_bucket,
output_key, vpc configs, launch config, etc and you can use those as the inputs for this example.

## Compiling the pipeline template

Follow the guide to [building a pipeline](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/) to install the Kubeflow Pipelines SDK, then run the following command to compile the sample Python into a workflow specification. The specification takes the form of a YAML file compressed into a `.tar.gz` file.

```bash
dsl-compile --py rlestimator_pipeline_custom_image.py --output rlestimator_pipeline_custom_image.tar.gz
dsl-compile --py rlestimator_pipeline_toolkit_image.py --output rlestimator_pipeline_toolkit_image.tar.gz
dsl-compile --py sagemaker_robomaker_rl_job.py --output sagemaker_robomaker_rl_job.tar.gz
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

RoboMaker Create Simulation Application:
  [source code](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/create_simulation_application/src)
