#!/bin/bash
# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

base_dir=$(pwd)
components_dir=$base_dir/components

# Build and push images of Kubeflow Pipelines components
for component in $components_dir/*/; do
    cd $component && ./build.sh
done

# Compile kubeflow pipeline tar file 
cd $base_dir/pipeline && ./build.sh
(mv -f src/*.tar.gz $base_dir && \
echo "Pipeline compiled sucessfully!") || \
echo "Pipeline compilation failed!"
