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

# Notice: caching is tricky when recursion is involved. Please be careful and 
# set proper max_cache_staleness in case of infinite loop.

import kfp
from kfp import dsl


def flip_coin_op():
    """Flip a coin and output heads or tails randomly."""
    return dsl.ContainerOp(
        name='Flip coin',
        image='python:alpine3.6',
        command=['sh', '-c'],
        arguments=['python -c "import random; result = \'heads\' if random.randint(0,1) == 0 '
                  'else \'tails\'; print(result)" | tee /tmp/output'],
        file_outputs={'output': '/tmp/output'}
    )


def print_op(msg):
    """Print a message."""
    return dsl.ContainerOp(
        name='Print',
        image='alpine:3.6',
        command=['echo', msg],
    )


# Use the dsl.graph_component to decorate pipeline functions that can be
# recursively called.
@dsl.graph_component
def flip_component(flip_result):
    print_flip = print_op(flip_result)
    flipA = flip_coin_op().after(print_flip)
    # set max_cache_staleness to 0 to prevent infinite loop due to caching
    flipA.execution_options.caching_strategy.max_cache_staleness = "P0D"
    with dsl.Condition(flipA.output == 'heads'):
        # When the flip_component is called recursively, the flipA.output
        # from inside the graph component will be passed to the next flip_component
        # as the input whereas the flip_result in the current graph component
        # comes from the flipA.output in the flipcoin function.
        flip_component(flipA.output)


@dsl.pipeline(
    name='Recursive loop pipeline',
    description='Shows how to create recursive loops.'
)
def flipcoin():
    first_flip = flip_coin_op()
    # set max_cache_staleness to 0 to prevent infinite loop due to caching
    first_flip.execution_options.caching_strategy.max_cache_staleness = "P0D"
    flip_loop = flip_component(first_flip.output)
    # flip_loop is a graph_component with the outputs field
    # filled with the returned dictionary.
    print_op('cool, it is over.').after(flip_loop)


if __name__ == '__main__':
    kfp.compiler.Compiler().compile(flipcoin, __file__ + '.yaml')
