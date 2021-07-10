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

def print_op(msg):
  """Print a message."""
  return dsl.ContainerOp(
      name='Print',
      image='alpine:3.6',
      command=['echo', msg],
  )

def add_annotation(op):
  op.add_pod_annotation(name='hobby', value='football')
  return op

@dsl.pipeline(
    name='Pipeline transformer',
    description='The pipeline shows how to apply functions to all ops in the pipeline by pipeline transformers'
)
def transform_pipeline():
  op1 = print_op('hey, what are you up to?')
  op2 = print_op('train my model.')
  dsl.get_pipeline_conf().add_op_transformer(add_annotation)

if __name__ == '__main__':
  kfp.compiler.Compiler().compile(transform_pipeline, __file__ + '.yaml')
