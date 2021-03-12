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


"""
This example demonstrates how to use ResourceOp to specify the value of env var.
"""

import json
import kfp
import kfp.dsl as dsl


_CONTAINER_MANIFEST = """
{
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {
        "generateName": "resourceop-basic-job-"
    },
    "spec": {
        "template": {
            "metadata": {
                "name": "resource-basic"
            },
            "spec": {
                "containers": [{
                    "name": "sample-container",
                    "image": "k8s.gcr.io/busybox",
                    "command": ["/usr/bin/env"]
                }],
                "restartPolicy": "Never"
            }
        },
        "backoffLimit": 4      
    }
}
"""


@dsl.pipeline(
    name="ResourceOp Basic",
    description="A Basic Example on ResourceOp Usage."
)
def resourceop_basic():

    # Start a container. Print out env vars.
    op = dsl.ResourceOp(
        name='test-step',
        k8s_resource=json.loads(_CONTAINER_MANIFEST),
        action='create'
    )


if __name__ == '__main__':
    kfp.compiler.Compiler().compile(resourceop_basic, __file__ + '.yaml')
