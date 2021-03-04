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

from kfp.v2 import dsl
from kfp.v2 import compiler
from kfp.v2 import components


def main(pipeline_root: str = 'gs://gongyuan-test/hello_world'):

    def hello_world(text: str):
        print(text)
        return text

    components.func_to_container_op(
        hello_world, output_component_file='hw.yaml'
    )

    # Create a pipeline op from the component we defined above.
    hw_op = components.load_component_from_file(
        './hw.yaml'
    )  # you can also use load_component_from_url

    @dsl.pipeline(name='hello-world', description='A simple intro pipeline')
    def pipeline_parameter_to_consumer(text: str = 'hi there'):
        '''Pipeline that passes small pipeline parameter string to consumer op'''
        consume_task = hw_op(
            text
        )  # Passing pipeline parameter as argument to consumer op

    pipeline_func = pipeline_parameter_to_consumer

    compiler.Compiler().compile(
        pipeline_func=pipeline_func,
        pipeline_root=pipeline_root,
        output_path='hw_pipeline_job.json'
    )


if __name__ == "__main__":
    # execute only if run as a script
    import fire
    fire.Fire(main)
