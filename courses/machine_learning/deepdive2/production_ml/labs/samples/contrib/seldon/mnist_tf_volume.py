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
    description="Example of training and serving seldon MNIST TF model. Like kubeflow/example-seldon but using existing images."
)

def mnist_tf_volume(docker_repo_training='seldonio/deepmnistclassifier_trainer',
             docker_tag_training='0.3',
             docker_repo_serving='seldonio/deepmnistclassifier_runtime',
             docker_tag_serving='0.3'):

#use volume for storing model
#here model is saved and mounted into pre-defined image for serving
#alternatively model can be baked into image - for that see mabdeploy-seldon.py
#requires seldon v0.3.0 or higher
    modelvolop = dsl.VolumeOp(
        name="modelpvc",
        resource_name="modelpvc",
        size="50Mi",
        modes=dsl.VOLUME_MODE_RWO
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
    )

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
    ).after(train)


if __name__ == "__main__":
    import kfp.compiler as compiler
    compiler.Compiler().compile(mnist_tf_volume, __file__ + ".tar.gz")
