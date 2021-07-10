#!/usr/bin/env python3
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

import kfp
import kfp.dsl as dsl

@dsl.pipeline(
    name="pipeline_with_sidecar", 
    description="A pipeline that demonstrates how to add a sidecar to an operation."
)
def pipeline_with_sidecar(sleep_sec: int = 30):

    # sidecar with sevice that reply "hello world" to any GET request
    echo = dsl.Sidecar(
        name="echo",
        image="hashicorp/http-echo:latest",
        args=['-text="hello world"'],
    )

    # container op with sidecar
    op1 = dsl.ContainerOp(
        name="download",
        image="busybox:latest",
        command=["sh", "-c"],
        arguments=[
            "sleep %s; wget localhost:5678 -O /tmp/results.txt" % sleep_sec
        ],  # sleep for X sec and call the sidecar and save results to output
        sidecars=[echo],
        file_outputs={"downloaded": "/tmp/results.txt"},
    )

    op2 = dsl.ContainerOp(
        name="echo",
        image="library/bash",
        command=["sh", "-c"],
        arguments=["echo %s" % op1.output],  # print out content of op1 output
    )

if __name__ == '__main__':
    kfp.compiler.Compiler().compile(pipeline_with_sidecar, __file__ + '.yaml')