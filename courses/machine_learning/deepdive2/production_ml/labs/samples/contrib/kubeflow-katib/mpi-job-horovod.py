# Kubeflow Pipeline with Katib component.

# In this example you will create Katib Experiment using Bayesian optimization algorithm.
# As a Trial template you will use Kubeflow MPIJob with Horovod mnist training container.
# After that, you will compile a Kubeflow Pipeline with your Katib Experiment.
# Use Kubeflow Pipelines UI to upload the Pipeline and create the Run.

# This Experiment is similar to this: https://github.com/kubeflow/katib/blob/master/examples/v1beta1/mpijob-horovod.yaml
# Check the training container source code here: https://github.com/kubeflow/mpi-operator/tree/master/examples/horovod.

# Note: To run this example, your Kubernetes cluster should run MPIJob operator.
# Follow this guide to install MPIJob on your cluster: https://www.kubeflow.org/docs/components/training/mpi/

# Note: You have to install kfp>=1.1.1 SDK and kubeflow-katib>=0.10.1 SDK to run this example.

import kfp
import kfp.dsl as dsl
from kfp import components

from kubeflow.katib import ApiClient
from kubeflow.katib import V1beta1ExperimentSpec
from kubeflow.katib import V1beta1AlgorithmSpec
from kubeflow.katib import V1beta1AlgorithmSetting
from kubeflow.katib import V1beta1ObjectiveSpec
from kubeflow.katib import V1beta1ParameterSpec
from kubeflow.katib import V1beta1FeasibleSpace
from kubeflow.katib import V1beta1TrialTemplate
from kubeflow.katib import V1beta1TrialParameterSpec


@dsl.pipeline(
    name="Launch Katib MPIJob Experiment",
    description="An example to launch Katib Experiment with MPIJob"
)
def horovod_mnist_hpo():
    # Experiment name and namespace.
    experiment_name = "mpi-horovod-mnist"
    experiment_namespace = "anonymous"

    # Trial count specification.
    max_trial_count = 6
    max_failed_trial_count = 3
    parallel_trial_count = 2

    # Objective specification.
    objective = V1beta1ObjectiveSpec(
        type="minimize",
        goal=0.01,
        objective_metric_name="loss",
    )

    # Algorithm specification.
    algorithm = V1beta1AlgorithmSpec(
        algorithm_name="bayesianoptimization",
        algorithm_settings=[
            V1beta1AlgorithmSetting(
                name="random_state",
                value="10"
            )
        ]
    )

    # Experiment search space.
    # In this example we tune learning rate and number of training steps.
    parameters = [
        V1beta1ParameterSpec(
            name="lr",
            parameter_type="double",
            feasible_space=V1beta1FeasibleSpace(
                min="0.001",
                max="0.003"
            ),
        ),
        V1beta1ParameterSpec(
            name="num-steps",
            parameter_type="int",
            feasible_space=V1beta1FeasibleSpace(
                min="50",
                max="150",
                step="10"
            ),
        ),
    ]

    # JSON template specification for the Trial's Worker Kubeflow MPIJob.
    trial_spec = {
        "apiVersion": "kubeflow.org/v1",
        "kind": "MPIJob",
        "spec": {
            "slotsPerWorker": 1,
            "cleanPodPolicy": "Running",
            "mpiReplicaSpecs": {
                "Launcher": {
                    "replicas": 1,
                    "template": {
                        "metadata": {
                            "annotations": {
                                "sidecar.istio.io/inject": "false"
                            }
                        },
                        "spec": {
                            "containers": [
                                {
                                    "image": "docker.io/kubeflow/mpi-horovod-mnist",
                                    "name": "mpi-launcher",
                                    "command": [
                                        "mpirun"
                                    ],
                                    "args": [
                                        "-np",
                                        "2",
                                        "--allow-run-as-root",
                                        "-bind-to",
                                        "none",
                                        "-map-by",
                                        "slot",
                                        "-x",
                                        "LD_LIBRARY_PATH",
                                        "-x",
                                        "PATH",
                                        "-mca",
                                        "pml",
                                        "ob1",
                                        "-mca",
                                        "btl",
                                        "^openib",
                                        "python",
                                        "/examples/tensorflow_mnist.py",
                                        "--lr",
                                        "${trialParameters.learningRate}",
                                        "--num-steps",
                                        "${trialParameters.numberSteps}"
                                    ],
                                    "resources": {
                                        "limits": {
                                            "cpu": "500m",
                                            "memory": "2Gi"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                },
                "Worker": {
                    "replicas": 2,
                    "template": {
                        "metadata": {
                            "annotations": {
                                "sidecar.istio.io/inject": "false"
                            }
                        },
                        "spec": {
                            "containers": [
                                {
                                    "image": "docker.io/kubeflow/mpi-horovod-mnist",
                                    "name": "mpi-worker",
                                    "resources": {
                                        "limits": {
                                            "cpu": "500m",
                                            "memory": "4Gi"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    }

    # Configure parameters for the Trial template.
    trial_template = V1beta1TrialTemplate(
        primary_pod_labels={
            "mpi-job-role": "launcher"
        },
        primary_container_name="mpi-launcher",
        success_condition='status.conditions.#(type=="Succeeded")#|#(status=="True")#',
        failure_condition='status.conditions.#(type=="Failed")#|#(status=="True")#',
        trial_parameters=[
            V1beta1TrialParameterSpec(
                name="learningRate",
                description="Learning rate for the training model",
                reference="lr"
            ),
            V1beta1TrialParameterSpec(
                name="numberSteps",
                description="Number of training steps",
                reference="num-steps"
            ),
        ],
        trial_spec=trial_spec
    )

    # Create Experiment specification.
    experiment_spec = V1beta1ExperimentSpec(
        max_trial_count=max_trial_count,
        max_failed_trial_count=max_failed_trial_count,
        parallel_trial_count=parallel_trial_count,
        objective=objective,
        algorithm=algorithm,
        parameters=parameters,
        trial_template=trial_template
    )

    # Get the Katib launcher.
    # Load component from the URL or from the file.
    katib_experiment_launcher_op = components.load_component_from_url(
        "https://raw.githubusercontent.com/kubeflow/pipelines/master/components/kubeflow/katib-launcher/component.yaml")
    # katib_experiment_launcher_op = components.load_component_from_file(
    #     "../../../components/kubeflow/katib-launcher/component.yaml"
    # )

    # Katib launcher component.
    # Experiment Spec should be serialized to a valid Kubernetes object.
    # The Experiment is deleted after the Pipeline is finished.
    op = katib_experiment_launcher_op(
        experiment_name=experiment_name,
        experiment_namespace=experiment_namespace,
        experiment_spec=ApiClient().sanitize_for_serialization(experiment_spec),
        experiment_timeout_minutes=60)

    # Output container to print the results.
    dsl.ContainerOp(
        name="best-hp",
        image="library/bash:4.4.23",
        command=["sh", "-c"],
        arguments=["echo Best HyperParameters: %s" % op.output],
    )


if __name__ == "__main__":
    kfp.compiler.Compiler().compile(horovod_mnist_hpo, __file__ + ".tar.gz")
