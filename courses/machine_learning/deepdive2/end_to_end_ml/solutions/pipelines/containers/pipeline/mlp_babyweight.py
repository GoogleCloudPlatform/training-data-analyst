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
import os

class ObjectDict(dict):
  def __getattr__(self, name):
    if name in self:
      return self[name]
    else:
      raise AttributeError("No such attribute: " + name)



    
    
    
    
@dsl.pipeline(
  name='babyweight',
  description='Train Babyweight model from scratch'
)
def preprocess_train_and_deploy(
    project='ai-analytics-solutions',
    bucket='ai-analytics-solutions-kfpdemo',
    start_year='2000'
):
    """End-to-end Pipeline to train and deploy babyweight model"""
    # Step 1: create training dataset using Apache Beam on Cloud Dataflow
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
    

    # Step 2: Do hyperparameter tuning of the model on Cloud ML Engine
    hparam_train = dsl.ContainerOp(
        name='hypertrain',
        # image needs to be a compile-time string
        image='gcr.io/ai-analytics-solutions/babyweight-pipeline-hypertrain:latest',
        arguments=[
            preprocess.outputs['bucket']
        ],
        file_outputs={'jobname': '/output.txt'}
      ).apply(use_gcp_secret('user-gcp-sa'))
    
    # core ML part of pipeline
    deploy_cmle = train_and_deploy_helper(preprocess, hparam_train)
    
    # Step 5: Deploy web app
    deploy_app = dsl.ContainerOp(
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

    # application URL will be https://ai-analytics-solutions.appspot.com/


@dsl.pipeline(
  name='babyweight',
  description='Train Babyweight model on current data in GCS'
)
def train_and_deploy(
    project='ai-analytics-solutions',
    bucket='ai-analytics-solutions-kfpdemo',
    start_year='2000'
):
    """Pipeline to retrain and deploy babyweight ML model only"""
    # Create dictionaries that correspond to output of previous steps
    preprocess = ObjectDict({
        'outputs': {
            'bucket': bucket
        }
    })
    
    # Step 2: hyperparam train
    hparam_train = ObjectDict({
      'outputs': {
        'jobname': os.environ.get('HPARAM_JOB', 'babyweight_200207_231639')
      }
    })
    
    # actual pipeline we want to run
    deploy_cmle = train_and_deploy_helper(preprocess, hparam_train)
    
    # no need to redeploy web app at https://ai-analytics-solutions.appspot.com/
    
    
    
def train_and_deploy_helper(preprocess, hparam_train):
    """Helper function called from the two pipeline functions"""
    
    # Step 3: Train the model some more, but on the pipelines cluster itself
    train_tuned = dsl.ContainerOp(
      name='traintuned',
      # image needs to be a compile-time string
      image='gcr.io/ai-analytics-solutions/babyweight-pipeline-traintuned:latest',
      arguments=[
        hparam_train.outputs['jobname'],
        preprocess.outputs['bucket']
      ],
      file_outputs={'train': '/output.txt'}
    ).apply(use_gcp_secret('user-gcp-sa'))
    train_tuned.set_memory_request('2G')
    train_tuned.set_cpu_request('1')

    # Step 4: Deploy the trained model to Cloud ML Engine
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

    return deploy_cmle


def finetune_and_deploy(filename):
    """invoked from a Cloud Function or a Cloud Run, it launches a Pipeline on kfp"""
    import kfp
    import sys
    
    if 'babyweight/preproc/train' in filename:
        PIPELINES_HOST = os.environ.get('PIPELINES_HOST', "Environment variable PIPELINES_HOST not set")
        PROJECT = os.environ.get('PROJECT', "Environment variable PROJECT not set")
        BUCKET = os.environ.get('BUCKET', "Environment variable BUCKET not set")
        print("New file {}: Launching ML pipeline on {} to finetune model in {}".format(
            filename, PIPELINES_HOST, BUCKET))
        sys.stdout.flush()
        client = kfp.Client(host=PIPELINES_HOST)
        args = {
            'project' : PROJECT, 
            'bucket' : BUCKET,
        }
        pipeline = client.create_run_from_pipeline_func(train_and_deploy, args)
        return 'Fine tuning job Launched!'

