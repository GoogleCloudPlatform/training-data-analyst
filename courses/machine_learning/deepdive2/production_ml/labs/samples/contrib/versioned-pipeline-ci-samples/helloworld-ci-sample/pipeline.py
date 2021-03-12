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
    name='hello world pipeline sample',
    description='A simple sample using curl to interact with kfp'
)
def helloworld_ci_pipeline():
  import os
  train_op = kfp.components.load_component_from_file('./component.yaml')
  train = train_op()

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(helloworld_ci_pipeline, __file__ + '.zip')
