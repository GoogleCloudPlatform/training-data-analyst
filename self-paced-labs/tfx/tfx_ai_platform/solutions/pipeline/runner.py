# Lint as: python2, python3
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""KFP runner configuration"""

import kfp

from tfx.orchestration import data_types
from tfx.orchestration.kubeflow import kubeflow_dag_runner

from typing import Optional, Dict, List, Text
from distutils.util import strtobool

from config import Config
from pipeline import create_pipeline

if __name__ == '__main__':

  # Set the values for the compile time parameters
  ai_platform_training_args = {
      'project': Config.PROJECT_ID,
      'region': Config.GCP_REGION,
      'serviceAccount': Config.CUSTOM_SERVICE_ACCOUNT,
      'masterConfig': {
          'imageUri': Config.TFX_IMAGE,
      }
  }

  ai_platform_serving_args = {
      'project_id': Config.PROJECT_ID,
      'model_name': Config.MODEL_NAME,
      'runtimeVersion': Config.RUNTIME_VERSION,
      'pythonVersion': Config.PYTHON_VERSION,
      'regions': [Config.GCP_REGION]
  }

  beam_tmp_folder = '{}/beam/tmp'.format(Config.ARTIFACT_STORE_URI)
  beam_pipeline_args = [
      '--runner=DataflowRunner',
      '--experiments=shuffle_mode=auto',
      '--project=' + Config.PROJECT_ID,
      '--temp_location=' + beam_tmp_folder,
      '--region=' + Config.GCP_REGION,
  ]
    
  
  # Set the default values for the pipeline runtime parameters   
  data_root_uri = data_types.RuntimeParameter(
      name='data-root-uri',
      default=Config.DATA_ROOT_URI,
      ptype=Text
  )

  train_steps = data_types.RuntimeParameter(
      name='train-steps',
      default=5000,
      ptype=int
  )
    
  eval_steps = data_types.RuntimeParameter(
      name='eval-steps',
      default=500,
      ptype=int
  )

  pipeline_root = '{}/{}/{}'.format(
      Config.ARTIFACT_STORE_URI, 
      Config.PIPELINE_NAME,
      kfp.dsl.RUN_ID_PLACEHOLDER)
    
  # Set KubeflowDagRunner settings.
  metadata_config = kubeflow_dag_runner.get_default_kubeflow_metadata_config()

  runner_config = kubeflow_dag_runner.KubeflowDagRunnerConfig(
      kubeflow_metadata_config = metadata_config,
      pipeline_operator_funcs = kubeflow_dag_runner.get_default_pipeline_operator_funcs(
          strtobool(Config.USE_KFP_SA)),
      tfx_image=Config.TFX_IMAGE)

  # Compile the pipeline.
  kubeflow_dag_runner.KubeflowDagRunner(config=runner_config).run(
      create_pipeline(
        pipeline_name=Config.PIPELINE_NAME,
        pipeline_root=pipeline_root,
        data_root_uri=data_root_uri,
        train_steps=train_steps,
        eval_steps=eval_steps,
        enable_tuning=strtobool(Config.ENABLE_TUNING),          
        ai_platform_training_args=ai_platform_training_args,
        ai_platform_serving_args=ai_platform_serving_args,
        beam_pipeline_args=beam_pipeline_args))
     
        




