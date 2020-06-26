#!/bin/bash
# Copyright 2019 Google Inc. All rights reserved.
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
export CSR_REPO_NAME=apm-qwiklabs-demo
export MASTER_BRANCH=master
export ERROR_BRANCH=APM-Troubleshooting-Demo-2 
date

# Create the source repo and link
gcloud source repos create $CSR_REPO_NAME

# Create the temporary dirs for the code
mkdir -p tmp/master
mkdir -p tmp/error
cd tmp/master
pwd
git clone https://github.com/blipzimmerman/microservices-demo-1 
cd microservices-demo-1
git remote add apm-demo https://source.developers.google.com/p/$DEVSHELL_PROJECT_ID/r/$CSR_REPO_NAME
git push apm-demo master

cd ../../error
git clone -b APM-Troubleshooting-Demo-2 https://github.com/blipzimmerman/microservices-demo-1 
cd microservices-demo-1
git remote add apm-demo-error https://source.developers.google.com/p/$DEVSHELL_PROJECT_ID/r/$CSR_REPO_NAME
git push apm-demo-error APM-Troubleshooting-Demo-2

# Clean everything up

cd ../../../
rm -rf tmp/master/*
rm -rf tmp/master/.*
rm -rf tmp/error/*
rm -rf tmp/error/.*
rmdir tmp/error tmp/master tmp
