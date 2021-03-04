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


import json
import kfp.dsl as dsl
from string import Template

@dsl.pipeline(
    name="Deploy example MAB",
    description="Multi-armed bandit example"
)
def mabdeploy_seldon(docker_image1='seldonio/mock_classifier:1.0',
                     docker_image2='seldonio/mock_classifier:1.0',
                     mab_router_image='seldonio/mab_epsilon_greedy:1.1'):

#serve two models load balanced as bandit as per https://github.com/SeldonIO/seldon-core/blob/master/notebooks/helm_examples.ipynb
#in this example no volumes or buckets required as the models are baked into images
#seldon can also be used with volumes - see seldon tf mnist example
    mabjson_template = Template("""
{
    "apiVersion": "machinelearning.seldon.io/v1alpha2",
    "kind": "SeldonDeployment",
    "metadata": {
        "labels": {
            "app": "seldon"
        },
        "name": "mnist-classifier-mab"
    },
    "spec": {
        "name": "mnist-classifier-mab",
        "predictors": [
            {
                "name": "abtest",
                "replicas": 1,
                "componentSpecs": [{
                    "spec": {
                        "containers": [
                            {
                                "image": "$image1",
                                "imagePullPolicy": "IfNotPresent",
                                "name": "classifier-1",
                                "resources": {
                                    "requests": {
                                        "memory": "1Mi"
                                    }
                                }
                            }],
                        "terminationGracePeriodSeconds": 20
                    }},
                {
                    "metadata":{
                        "labels":{
                            "version":"v2"
                        }
                    },    
                        "spec":{
                            "containers":[
                            {
                                "image": "$image2",
                                "imagePullPolicy": "IfNotPresent",
                                "name": "classifier-2",
                                "resources": {
                                    "requests": {
                                        "memory": "1Mi"
                                    }
                                }
                            }
                        ],
                        "terminationGracePeriodSeconds": 20
                        }
                },
                {
                    "spec":{
                        "containers": [{
                            "image": "$router",
                            "name": "eg-router"
                        }],
                        "terminationGracePeriodSeconds": 20
                    }}
                ],
                "graph": {
                    "name": "eg-router",
                    "type":"ROUTER",
                    "parameters": [
                        {
                            "name": "n_branches",
                            "value": "2",
                            "type": "INT"
                        },
                        {
                            "name": "epsilon",
                            "value": "0.2",
                            "type": "FLOAT"
                        },
                        {
                            "name": "verbose",
                            "value": "1",
                            "type": "BOOL"
                        }
                    ],
                    "children": [
                        {
                            "name": "classifier-1",
                            "endpoint":{
                                "type":"REST"
                            },
                            "type":"MODEL",
                            "children":[]
                        },
                        {
                            "name": "classifier-2",
                            "endpoint":{
                                "type":"REST"
                            },
                            "type":"MODEL",
                            "children":[]
                        }   
                    ]
                }
            }
        ]
    }
}
""")

    mabjson = mabjson_template.substitute({ 'image1': str(docker_image1),'image2': str(docker_image2),'router': str(mab_router_image)})

    mabdeployment = json.loads(mabjson)

    deploy = dsl.ResourceOp(
        name="deploy",
        k8s_resource=mabdeployment,
        action="apply",
        success_condition='status.state == Available'
    )


if __name__ == "__main__":
    import kfp.compiler as compiler
    compiler.Compiler().compile(mabdeploy_seldon, __file__ + ".tar.gz")
