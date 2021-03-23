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

IMAGE="kubeflow-pipeline"
PV=src/persistent-volume.yaml
PVC=src/persistent-volume-claim.yaml
# Modify according to your persistent volume yaml
PERSISTENT_VOL_PATH=/mnt/workspace

sudo mkdir -p $PERSISTENT_VOL_PATH

# Mount persistent volume
kubectl replace -f $PV 2>/dev/null || kubectl apply -f $PV 
kubectl replace -f $PVC 2>/dev/null || kubectl apply -f $PVC

docker build -t $IMAGE .
docker run --rm -v $(pwd)/src:/workspace $IMAGE
