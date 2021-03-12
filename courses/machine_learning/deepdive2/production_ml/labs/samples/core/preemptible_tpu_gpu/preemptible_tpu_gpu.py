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
"""This is a simple toy example demonstrating how to use preemptible computing resources."""

from kfp import dsl
from kfp import gcp


class FlipCoinOp(dsl.ContainerOp):
  """Flip a coin and output heads or tails randomly."""

  def __init__(self):
    super(FlipCoinOp, self).__init__(
        name='Flip',
        image='python:alpine3.6',
        command=['sh', '-c'],
        arguments=[
            'python -c "import random; result = \'heads\' if random.randint(0,1) == 0 '
            'else \'tails\'; print(result)" | tee /tmp/output'
        ],
        file_outputs={'output': '/tmp/output'})


@dsl.pipeline(
    name='pipeline flip coin', description='shows how to use dsl.Condition.')
def flipcoin():
  flip = FlipCoinOp().apply(gcp.use_preemptible_nodepool()).set_gpu_limit(
      1, 'nvidia').set_retry(5)


if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(flipcoin, __file__ + '.yaml')
