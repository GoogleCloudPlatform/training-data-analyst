#!/usr/bin/env python3
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

# %% [markdown]
# # Data passing tutorial
# Data passing is the most important aspect of Pipelines.
# 
# In Kubeflow Pipelines, the pipeline authors compose pipelines by creating component instances (tasks) and connecting them together.
# 
# Component have inputs and outputs. They can consume and produce arbitrary data.
# 
# Pipeline authors establish connections between component tasks by connecting their data inputs and outputs - by passing the output of one task as an argument to another task's input.
# 
# The system takes care of storing the data produced by components and later passing that data to other components for consumption as instructed by the pipeline.
# 
# This tutorial shows how to create python components that produce, consume and transform data.
# It shows how to create data passing pipelines by instantiating components and connecting them together.

# %%
from typing import NamedTuple

import kfp
from kfp.components import func_to_container_op, InputPath, OutputPath

# %% [markdown]
# ## Small data
# 
# Small data is the data that you'll be comfortable passing as program's command-line argument. Small data size should not exceed few kilobytes.
# 
# Some examples of typical types of small data are: number, URL, small string (e.g. column name).
# 
# Small lists, dictionaries and JSON structures are fine, but keep an eye on the size and consider switching to file-based data passing methods taht are more suitable for bigger data (more than several kilobytes) or binary data.
# 
# All small data outputs will be at some point serialized to strings and all small data input values will be at some point deserialized from strings (passed as command-line argumants). There are built-in serializers and deserializers for several common types (e.g. `str`, `int`, `float`, `bool`, `list`, `dict`). All other types of data need to be serialized manually before returning the data. Make sure to properly specify type annotations, otherwize there would be no automatic deserialization and the component function will receive strings instead of deserialized objects.

# %% [markdown]
# ## Bigger data (files)
# 
# Bigger data should be read from files and written to files.
# 
# The paths for the input and output files are chosen by the system and are passed into the function (as strings).
# 
# Use the `InputPath` parameter annotation to tell the system that the function wants to consume the corresponding input data as a file. The system will download the data, write it to a local file and then pass the **path** of that file to the function.
# 
# Use the `OutputPath` parameter annotation to tell the system that the function wants to produce the corresponding output data as a file. The system will prepare and pass the **path** of a file where the function should write the output data. After the function exits, the system will upload the data to the storage system so that it can be passed to downstream components.
# 
# You can specify the type of the consumed/produced data by specifying the type argument to `InputPath` and `OutputPath`. The type can be a python type or an arbitrary type name string. `OutputPath('TFModel')` means that the function states that the data it has written to a file has type 'TFModel'. `InputPath('TFModel')` means that the function states that it expect the data it reads from a file to have type 'TFModel'. When the pipeline author connects inputs to outputs the system checks whether the types match.
# 
# Note on input/output names: When the function is converted to component, the input and output names generally follow the parameter names, but the "\_path" and "\_file" suffixes are stripped from file/path inputs and outputs. E.g. the `number_file_path: InputPath(int)` parameter becomes the `number: int` input. This makes the argument passing look more natural: `number=42` instead of `number_file_path=42`.
# %% [markdown]
# 
# ### Writing and reading bigger data

# %%
# Writing bigger data
@func_to_container_op
def repeat_line(line: str, output_text_path: OutputPath(str), count: int = 10):
    '''Repeat the line specified number of times'''
    with open(output_text_path, 'w') as writer:
        for i in range(count):
            writer.write(line + '\n')


# Reading bigger data
@func_to_container_op
def print_text(text_path: InputPath()): # The "text" input is untyped so that any data can be printed
    '''Print text'''
    with open(text_path, 'r') as reader:
        for line in reader:
            print(line, end = '')

def print_repeating_lines_pipeline():
    repeat_lines_task = repeat_line(line='Hello', count=5000)
    print_text(repeat_lines_task.output) # Don't forget .output !

# Submit the pipeline for execution:
#kfp.Client(host=kfp_endpoint).create_run_from_pipeline_func(print_repeating_lines_pipeline, arguments={})

# %% [markdown]
# ### Processing bigger data

# %%
@func_to_container_op
def split_text_lines(source_path: InputPath(str), odd_lines_path: OutputPath(str), even_lines_path: OutputPath(str)):
    with open(source_path, 'r') as reader:
        with open(odd_lines_path, 'w') as odd_writer:
            with open(even_lines_path, 'w') as even_writer:
                while True:
                    line = reader.readline()
                    if line == "":
                        break
                    odd_writer.write(line)
                    line = reader.readline()
                    if line == "":
                        break
                    even_writer.write(line)

def text_splitting_pipeline():
    text = '\n'.join(['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'])
    split_text_task = split_text_lines(text)
    print_text(split_text_task.outputs['odd_lines'])
    print_text(split_text_task.outputs['even_lines'])

# Submit the pipeline for execution:
#kfp.Client(host=kfp_endpoint).create_run_from_pipeline_func(text_splitting_pipeline, arguments={})


# %% [markdown]
# ### Example: Pipeline that generates then sums many numbers

# %%
# Writing many numbers
@func_to_container_op
def write_numbers(numbers_path: OutputPath(str), start: int = 0, count: int = 10):
    with open(numbers_path, 'w') as writer:
        for i in range(start, count):
            writer.write(str(i) + '\n')


# Reading and summing many numbers
@func_to_container_op
def sum_numbers(numbers_path: InputPath(str)) -> int:
    sum = 0
    with open(numbers_path, 'r') as reader:
        for line in reader:
            sum = sum + int(line)
    return sum



# Pipeline to sum 100000 numbers
def sum_pipeline(count: int = 100000):
    numbers_task = write_numbers(count=count)
    print_text(numbers_task.output)

    sum_task = sum_numbers(numbers_task.outputs['numbers'])
    print_text(sum_task.output)


# Submit the pipeline for execution:
#kfp.Client(host=kfp_endpoint).create_run_from_pipeline_func(sum_pipeline, arguments={})

# Combining all pipelines together in a single pipeline
def file_passing_pipelines():
    print_repeating_lines_pipeline()
    text_splitting_pipeline()
    sum_pipeline()


if __name__ == '__main__':
    # Compiling the pipeline
    kfp.compiler.Compiler().compile(file_passing_pipelines, __file__ + '.yaml')
