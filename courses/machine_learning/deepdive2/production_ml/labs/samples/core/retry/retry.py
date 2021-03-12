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
from kfp import dsl


def random_failure_op(exit_codes):
    """A component that fails randomly."""
    return dsl.ContainerOp(
        name='random_failure',
        image='python:alpine3.6',
        command=['python', '-c'],
        arguments=['import random; import sys; exit_code = int(random.choice(sys.argv[1].split(","))); print(exit_code); sys.exit(exit_code)', exit_codes]
    )


@dsl.pipeline(
    name='Retry random failures',
    description='The pipeline includes two steps which fail randomly. It shows how to use ContainerOp(...).set_retry(...).'
)
def retry_sample_pipeline():
    op1 = random_failure_op('0,1,2,3').set_retry(10)
    op2 = random_failure_op('0,1').set_retry(5)


if __name__ == '__main__':
    kfp.compiler.Compiler().compile(retry_sample_pipeline, __file__ + '.yaml')
