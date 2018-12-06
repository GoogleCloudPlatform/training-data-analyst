#!/usr/bin/env python3
# Copyright 2018 Google LLC
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


import kfp.dsl as dsl

class ObjectDict(dict):
  def __getattr__(self, name):
    if name in self:
      return self[name]
    else:
      raise AttributeError("No such attribute: " + name)


@dsl.pipeline(
  name='babyweight',
  description='Train Babyweight model'
)
def train_and_deploy(
    project='cloud-training-demos',
    bucket='cloud-training-demos-ml',
    startYear='2000'
):
  """Pipeline to train babyweight model"""
  start_step = 1

  # Step 1: create training dataset using Apache Beam on Cloud Dataflow
  if start_step <= 1:
    preprocess = dsl.ContainerOp(
      name='preprocess',
      # image needs to be a compile-time string
      image='gcr.io/cloud-training-demos/babyweight-pipeline-bqtocsv:latest',
      arguments=[
        '--project', project,
        '--mode', 'cloud',
        '--bucket', bucket,
        '--start_year', startYear
      ],
      file_outputs={'bucket': '/output.txt'}
    )
  else:
    preprocess = ObjectDict({
      'outputs': {
        'bucket': bucket
      }
    })

  # Step 2: Do hyperparameter tuning of the model on Cloud ML Engine
  if start_step <= 2:
    hparam_train = dsl.ContainerOp(
      name='hypertrain',
      # image needs to be a compile-time string
      image='gcr.io/cloud-training-demos/babyweight-pipeline-hypertrain:latest',
      arguments=[
        preprocess.outputs['bucket']
      ],
      file_outputs={'jobname': '/output.txt'}
    )
  else:
    hparam_train = ObjectDict({
      'outputs': {
        'jobname': 'babyweight_181008_210829'
      }
    })

  # Step 3: Train the model some more, but on the pipelines cluster itself
  if start_step <= 3:
    train_tuned = dsl.ContainerOp(
      name='traintuned',
      # image needs to be a compile-time string
      image='gcr.io/cloud-training-demos/babyweight-pipeline-traintuned-trainer:latest',
      #image='gcr.io/cloud-training-demos/babyweight-pipeline-traintuned-trainer@sha256:3d73c805430a16d0675aeafa9819d6d2cfbad0f0f34cff5fb9ed4e24493bc9a8',
      arguments=[
        hparam_train.outputs['jobname'],
        bucket
      ],
      file_outputs={'train': '/output.txt'}
    )
    train_tuned.set_memory_request('2G')
    train_tuned.set_cpu_request('1')
  else:
    train_tuned = ObjectDict({
        'outputs': {
          'train': 'gs://cloud-training-demos-ml/babyweight/hyperparam/15'
        }
    })


  # Step 4: Deploy the trained model to Cloud ML Engine
  if start_step <= 4:
    deploy_cmle = dsl.ContainerOp(
      name='deploycmle',
      # image needs to be a compile-time string
      image='gcr.io/cloud-training-demos/babyweight-pipeline-deploycmle:latest',
      arguments=[
        train_tuned.outputs['train'],  # modeldir
        'babyweight',
        'mlp'
      ],
      file_outputs={
        'model': '/model.txt',
        'version': '/version.txt'
      }
    )
  else:
    deploy_cmle = ObjectDict({
      'outputs': {
        'model': 'babyweight',
        'version': 'mlp'
      }
    })

  # Step 5: Deploy the trained model to AppEngine
  if start_step <= 5:
    deploy_cmle = dsl.ContainerOp(
      name='deployapp',
      # image needs to be a compile-time string
      image='gcr.io/cloud-training-demos/babyweight-pipeline-deployapp:latest',
      arguments=[
        deploy_cmle.outputs['model'],
        deploy_cmle.outputs['version']
      ],
      file_outputs={
        'appurl': '/appurl.txt'
      }
    )
  else:
    deploy_cmle = ObjectDict({
      'outputs': {
        'appurl': 'https://cloud-training-demos.appspot.com/'
      }
    })


if __name__ == '__main__':
  import kfp.compiler as compiler
  import sys
  if len(sys.argv) != 2:
    print("Usage: mlp_babyweight  pipeline-output-name")
    sys.exit(-1)
  
  filename = sys.argv[1]
  compiler.Compiler().compile(train_and_deploy, filename)
