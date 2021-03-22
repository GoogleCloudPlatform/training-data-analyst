# Copyright 2021 Google LLC
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

PIPELINE_ROOT = 'gs://gongyuan-test/pipeline_root/'

# Simple two-step pipeline with 'producer' and 'consumer' steps
from kfp.v2 import components
from kfp.v2 import compiler
from kfp.v2 import dsl

producer_op = components.load_component_from_text(
    """
name: Producer
inputs:
- {name: input_text, type: String, description: 'Represents an input parameter.'}
outputs:
- {name: output_value, type: String, description: 'Represents an output paramter.'}
implementation:
  container:
    image: google/cloud-sdk:latest
    command:
    - sh
    - -c
    - |
      set -e -x
      echo "$0, this is an output parameter" | gsutil cp - "$1"
    - {inputValue: input_text}
    - {outputPath: output_value}
"""
)

consumer_op = components.load_component_from_text(
    """
name: Consumer
inputs:
- {name: input_value, type: String, description: 'Represents an input parameter. It connects to an upstream output parameter.'}
implementation:
  container:
    image: google/cloud-sdk:latest
    command:
    - sh
    - -c
    - |
      set -e -x
      echo "Read from an input parameter: " && echo "$0"
    - {inputValue: input_value}
"""
)


@dsl.pipeline(name='simple-two-step-pipeline')
def two_step_pipeline(text='Hello world'):
    producer = producer_op(input_text=text)
    consumer = consumer_op(input_value=producer.outputs['output_value'])


compiler.Compiler().compile(
    pipeline_func=two_step_pipeline,
    pipeline_root=PIPELINE_ROOT,
    output_path='two_step_pipeline_job.json'
)
