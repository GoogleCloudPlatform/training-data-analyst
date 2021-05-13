# Copyright 2020 Google LLC
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

# This sample shows how components can output directories
# Outputting a directory is performed the same way as outputting a file:
# component receives an output path, writes data at that path and the system takes that data and makes it available for the downstream components.
# To output a file, create a new file at the output path location.
# To output a directory, create a new directory at the output path location.


import kfp
from kfp.components import create_component_from_func, load_component_from_text, InputPath, OutputPath


# Outputting directories from Python-based components:

@create_component_from_func
def produce_dir_with_files_python_op(output_dir_path: OutputPath(), num_files: int = 10):
    import os
    os.makedirs(output_dir_path, exist_ok=True)
    for i in range(num_files):
        file_path = os.path.join(output_dir_path, str(i) + '.txt')
        with open(file_path, 'w') as f:
            f.write(str(i))


@create_component_from_func
def list_dir_files_python_op(input_dir_path: InputPath()):
    import os
    dir_items = os.listdir(input_dir_path)
    for dir_item in dir_items:
        print(dir_item)


# Outputting directories from general command-line based components:

produce_dir_with_files_general_op = load_component_from_text('''
name: Produce directory
inputs:
- {name: num_files, type: Integer}
outputs:
- {name: output_dir}
implementation:
  container:
    image: alpine
    command:
    - sh
    - -ecx
    - |
      num_files="$0"
      output_path="$1"
      mkdir -p "$output_path"
      for i in $(seq "$num_files"); do
        echo "$i" > "$output_path/${i}.txt"
      done
    - {inputValue: num_files}
    - {outputPath: output_dir}
''')


list_dir_files_general_op = load_component_from_text('''
name: List dir files
inputs:
- {name: input_dir}
implementation:
  container:
    image: alpine
    command:
    - ls
    - {inputPath: input_dir}
''')


# Test pipeline

def dir_pipeline():
    produce_dir_python_task = produce_dir_with_files_python_op(num_files=15)
    list_dir_files_python_op(input_dir=produce_dir_python_task.output)

    produce_dir_general_task = produce_dir_with_files_general_op(num_files=15)
    list_dir_files_general_op(input_dir=produce_dir_general_task.output)


if __name__ == '__main__':
    kfp_endpoint=None
    kfp.Client(host=kfp_endpoint).create_run_from_pipeline_func(dir_pipeline, arguments={})
