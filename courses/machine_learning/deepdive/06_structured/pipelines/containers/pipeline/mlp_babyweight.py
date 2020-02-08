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

from kfp.gcp import use_gcp_secret
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
    project='ai-analytics-solutions',
    bucket='ai-analytics-solutions-kfpdemo',
    start_year='2000',
    start_step=1
):
  """Pipeline to train babyweight model"""

  # Step 1: create training dataset using Apache Beam on Cloud Dataflow
  if start_step <= 1:
    preprocess = dsl.ContainerOp(
      name='preprocess',
      # image needs to be a compile-time string
      image='gcr.io/ai-analytics-solutions/babyweight-pipeline-bqtocsv:latest',
      arguments=[
        '--project', project,
        '--mode', 'cloud',
        '--bucket', bucket,
        '--start_year', start_year
      ],
      file_outputs={'bucket': '/output.txt'}
    ).apply(use_gcp_secret('user-gcp-sa'))
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
      image='gcr.io/ai-analytics-solutions/babyweight-pipeline-hypertrain:latest',
      arguments=[
        preprocess.outputs['bucket']
      ],
      file_outputs={'jobname': '/output.txt'}
    ).apply(use_gcp_secret('user-gcp-sa'))
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
      image='gcr.io/ai-analytics-solutions/babyweight-pipeline-traintuned:latest',
      arguments=[
        hparam_train.outputs['jobname'],
        bucket
      ],
      file_outputs={'train': '/output.txt'}
    ).apply(use_gcp_secret('user-gcp-sa'))
    train_tuned.set_memory_request('2G')
    train_tuned.set_cpu_request('1')
  else:
    train_tuned = ObjectDict({
        'outputs': {
          'train': 'gs://ai-analytics-solutions-kfpdemo/babyweight/hyperparam/17'
        }
    })


  # Step 4: Deploy the trained model to Cloud ML Engine
  if start_step <= 4:
    deploy_cmle = dsl.ContainerOp(
      name='deploycmle',
      # image needs to be a compile-time string
      image='gcr.io/ai-analytics-solutions/babyweight-pipeline-deploycmle:latest',
      arguments=[
        train_tuned.outputs['train'],  # modeldir
        'babyweight',
        'mlp'
      ],
      file_outputs={
        'model': '/model.txt',
        'version': '/version.txt'
      }
    ).apply(use_gcp_secret('user-gcp-sa'))
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
      image='gcr.io/ai-analytics-solutions/babyweight-pipeline-deployapp:latest',
      arguments=[
        deploy_cmle.outputs['model'],
        deploy_cmle.outputs['version']
      ],
      file_outputs={
        'appurl': '/appurl.txt'
      }
    ).apply(use_gcp_secret('user-gcp-sa'))
  else:
    deploy_cmle = ObjectDict({
      'outputs': {
        'appurl': 'https://ai-analytics-solutions.appspot.com/'
      }
    })


def finetune_and_deploy(filename):
    import kfp
    import os
    
    if 'babyweight/preproc/train' in filename:
        PIPELINES_HOST = os.getenv('PIPELINES_HOST')
        PROJECT = os.getenv('PROJECT')
        BUCKET = os.getenv('BUCKET')
        print("New file {}: Launching ML pipeline on {} to finetune model in {}",
              filename,
              PIPELINES_HOST,
              BUCKET
             )    
        client = kfp.Client(host=PIPELINES_HOST)
        args = {
            'project' : PROJECT, 
            'bucket' : BUCKET,
            'start_step' : 3
        }
        pipeline = client.create_run_from_pipeline_func(train_and_deploy, args)
        return 'Fine tuning job Launched!'

