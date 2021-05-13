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
    name="Deploy example SKLearn Iris",
    description="SKLearn Iris simple deployment example"
)
def iris_storagebucket(bucket='gs://seldon-models/sklearn/iris'):

#simple serving of an iris sklearn model based on https://docs.seldon.io/projects/seldon-core/en/latest/servers/overview.html
#requires seldon 0.3.2 or higher
    sklearnjson_template = Template("""
{
	"apiVersion": "machinelearning.seldon.io/v1alpha2",
	"kind": "SeldonDeployment",
	"metadata": {
		"name": "sklearn"
	},
	"spec": {
		"name": "iris",
		"predictors": [
			{
				"graph": {
					"children": [],
					"implementation": "SKLEARN_SERVER",
					"modelUri": "$bucket",
					"name": "classifier"
				},
				"name": "default",
				"replicas": 1
			}
		]
	}
}
""")

    sklearnjson = sklearnjson_template.substitute({ 'bucket': str(bucket)})

    sklearndeployment = json.loads(sklearnjson)

    deploy = dsl.ResourceOp(
        name="deploy",
        k8s_resource=sklearndeployment,
        action="apply",
        success_condition='status.state == Available'
    )


if __name__ == "__main__":
    import kfp.compiler as compiler
    compiler.Compiler().compile(iris_storagebucket, __file__ + ".tar.gz")
