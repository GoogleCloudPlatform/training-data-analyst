# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kubernetes import client as k8s_client
import kfp.dsl as dsl
import json
from string import Template

@dsl.pipeline(
    name="Seldon MNIST TF",
    description="Example of training and serving seldon MNIST TF model. Requires docker secret as per kubeflow/example-seldon. Simpler version is mnist_tf_nopush.py"
)

#Example derived from https://github.com/kubeflow/example-seldon
#This example is TF but R and SKLearn flows are similar - see kubeflow/example-seldon
#push access needed to chosen docker repo - see note below on secret
#requires seldon v0.3.0 or higher
def mnist_tf(docker_secret='docker-config',
             training_repo='https://github.com/kubeflow/example-seldon.git',
             training_branch='master',
             training_files='./example-seldon/models/tf_mnist/train/*',
             docker_repo_training='seldonio/deepmnistclassifier_trainer',
             docker_tag_training='0.3',
             serving_repo='https://github.com/kubeflow/example-seldon.git',
             serving_branch='master',
             serving_files='./example-seldon/models/tf_mnist/runtime/*',
             docker_repo_serving='seldonio/deepmnistclassifier_runtime',
             docker_tag_serving='0.3'):

#will be pushing image so need docker secret
#create from local with `kubectl create secret generic docker-config --from-file=config.json=${DOCKERHOME}/config.json --type=kubernetes.io/config`
    secret = k8s_client.V1Volume(
        name="docker-config-secret",
        secret=k8s_client.V1SecretVolumeSource(secret_name=docker_secret)
    )

#use volume for storing model
    modelvolop = dsl.VolumeOp(
        name="modelpvc",
        resource_name="modelpvc",
        size="50Mi",
        modes=dsl.VOLUME_MODE_RWO
    )
#and another as working directory between steps
    wkdirop = dsl.VolumeOp(
        name="wkdirpvc",
        resource_name="wkdirpvc",
        size="50Mi",
        modes=dsl.VOLUME_MODE_RWO
    )

#clone the training code and move to workspace dir as kaniko (next step) expects that
    clone = dsl.ContainerOp(
        name="clone",
        image="alpine/git:latest",
        command=["sh", "-c"],
        arguments=["git clone --depth 1 --branch "+str(training_branch)+" "+str(training_repo)+"; cp "+str(training_files)+" /workspace; ls /workspace/;"],
        pvolumes={"/workspace": wkdirop.volume}
    )

#build and push image for training
    build = dsl.ContainerOp(
        name="build",
        image="gcr.io/kaniko-project/executor:latest",
        arguments=["--dockerfile","Dockerfile","--destination",str(docker_repo_training)+":"+str(docker_tag_training)],
        pvolumes={"/workspace": clone.pvolume,"/root/.docker/": secret}
    )

    tfjobjson_template = Template("""
{
	"apiVersion": "kubeflow.org/v1beta1",
	"kind": "TFJob",
	"metadata": {
		"name": "mnist-train-{{workflow.uid}}",
		"ownerReferences": [
		{
			"apiVersion": "argoproj.io/v1alpha1",
			"kind": "Workflow",
			"controller": true,
			"name": "{{workflow.name}}",
			"uid": "{{workflow.uid}}"
		}
	    ]
	},
	"spec": {
		"tfReplicaSpecs": {
			"Worker": {
				"replicas": 1,
				"template": {
					"spec": {
						"containers": [
							{
								"image": "$dockerrepotraining:$dockertagtraining",
								"name": "tensorflow",
								"volumeMounts": [
									{
										"mountPath": "/data",
										"name": "persistent-storage"
									}
								]
							}
						],
						"restartPolicy": "OnFailure",
						"volumes": [
							{
								"name": "persistent-storage",
								"persistentVolumeClaim": {
									"claimName": "$modelpvc"
								}
							}
						]
					}
				}
			}
		}
	}
}
""")

    tfjobjson = tfjobjson_template.substitute({ 'dockerrepotraining': str(docker_repo_training),'dockertagtraining': str(docker_tag_training),'modelpvc': modelvolop.outputs["name"]})

    tfjob = json.loads(tfjobjson)

    train = dsl.ResourceOp(
        name="train",
        k8s_resource=tfjob,
        success_condition='status.replicaStatuses.Worker.succeeded == 1'
    ).after(build)

#prepare the serving code
    clone_serving = dsl.ContainerOp(
        name="clone_serving",
        image="alpine/git:latest",
        command=["sh", "-c"],
        arguments=["rm -rf /workspace/*; git clone --depth 1 --branch "+str(serving_branch)+" "+str(serving_repo)+"; cp "+str(serving_files)+" /workspace; ls /workspace/;"],
        pvolumes={"/workspace": wkdirop.volume}
    ).after(train)

    build_serving = dsl.ContainerOp(
        name="build_serving",
        image="gcr.io/kaniko-project/executor:latest",
        arguments=["--dockerfile","Dockerfile","--destination",str(docker_repo_serving)+":"+str(docker_tag_serving)],
        pvolumes={"/workspace": clone_serving.pvolume,"/root/.docker/": secret}
    ).after(clone_serving)

    seldon_serving_json_template = Template("""
{
	"apiVersion": "machinelearning.seldon.io/v1alpha2",
	"kind": "SeldonDeployment",
	"metadata": {
		"labels": {
			"app": "seldon"
		},
		"name": "mnist-classifier"
	},
	"spec": {
		"annotations": {
			"deployment_version": "v1",
			"project_name": "MNIST Example"
		},
		"name": "mnist-classifier",
		"predictors": [
			{
				"annotations": {
					"predictor_version": "v1"
				},
				"componentSpecs": [
					{
						"spec": {
							"containers": [
								{
									"image": "$dockerreposerving:$dockertagserving",
									"imagePullPolicy": "Always",
									"name": "mnist-classifier",
									"volumeMounts": [
										{
											"mountPath": "/data",
											"name": "persistent-storage"
										}
									]
								}
							],
							"terminationGracePeriodSeconds": 1,
							"volumes": [
								{
									"name": "persistent-storage",
									"persistentVolumeClaim": {
											"claimName": "$modelpvc"
									}
								}
							]
						}
					}
				],
				"graph": {
					"children": [],
					"endpoint": {
						"type": "REST"
					},
					"name": "mnist-classifier",
					"type": "MODEL"
				},
				"name": "mnist-classifier",
				"replicas": 1
			}
		]
	}
}    
""")
    seldon_serving_json = seldon_serving_json_template.substitute({ 'dockerreposerving': str(docker_repo_serving),'dockertagserving': str(docker_tag_serving),'modelpvc': modelvolop.outputs["name"]})

    seldon_deployment = json.loads(seldon_serving_json)

    serve = dsl.ResourceOp(
        name='serve',
        k8s_resource=seldon_deployment,
        success_condition='status.state == Available'
    ).after(build_serving)


if __name__ == "__main__":
    import kfp.compiler as compiler
    compiler.Compiler().compile(mnist_tf, __file__ + ".tar.gz")
