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


import kfp.dsl as dsl
import kfp.gcp as gcp
import kfp.components as comp
from kfp.dsl.types import GCSPath, String


COPY_ACTION = 'copy_data'
TRAIN_ACTION = 'train'
WORKSPACE_NAME = 'ws_gh_summ'
DATASET = 'dataset'
MODEL = 'model'

copydata_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/kubeflow/examples/master/github_issue_summarization/pipelines/components/t2t/datacopy_component.yaml'  # pylint: disable=line-too-long
  )

train_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/kubeflow/examples/master/github_issue_summarization/pipelines/components/t2t/train_component.yaml' # pylint: disable=line-too-long
  )

metadata_log_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/kubeflow/examples/master/github_issue_summarization/pipelines/components/t2t/metadata_log_component.yaml' # pylint: disable=line-too-long
  )

@dsl.pipeline(
  name='Github issue summarization',
  description='Demonstrate Tensor2Tensor-based training and TF-Serving'
)
def gh_summ(  #pylint: disable=unused-argument
  train_steps: 'Integer' = 2019300,
  project: String = 'YOUR_PROJECT_HERE',
  github_token: String = 'YOUR_GITHUB_TOKEN_HERE',
  working_dir: GCSPath = 'gs://YOUR_GCS_DIR_HERE',
  checkpoint_dir: GCSPath = 'gs://aju-dev-demos-codelabs/kubecon/model_output_tbase.bak2019000/',
  deploy_webapp: String = 'true',
  data_dir: GCSPath = 'gs://aju-dev-demos-codelabs/kubecon/t2t_data_gh_all/'
  ):


  copydata = copydata_op(
    data_dir=data_dir,
    checkpoint_dir=checkpoint_dir,
    model_dir='%s/%s/model_output' % (working_dir, dsl.RUN_ID_PLACEHOLDER),
    action=COPY_ACTION,
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))


  log_dataset = metadata_log_op(
    log_type=DATASET,
    workspace_name=WORKSPACE_NAME,
    run_name=dsl.RUN_ID_PLACEHOLDER,
    data_uri=data_dir
    )

  train = train_op(
    data_dir=data_dir,
    model_dir=copydata.outputs['copy_output_path'],
    action=TRAIN_ACTION, train_steps=train_steps,
    deploy_webapp=deploy_webapp
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))


  log_model = metadata_log_op(
    log_type=MODEL,
    workspace_name=WORKSPACE_NAME,
    run_name=dsl.RUN_ID_PLACEHOLDER,
    model_uri=train.outputs['train_output_path']
    )

  serve = dsl.ContainerOp(
      name='serve',
      image='gcr.io/google-samples/ml-pipeline-kubeflow-tfserve:v2',
      arguments=["--model_name", 'ghsumm-%s' % (dsl.RUN_ID_PLACEHOLDER,),
          "--model_path", train.outputs['train_output_path']
          ]
      ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  log_dataset.after(copydata)
  log_model.after(train)
  train.set_gpu_limit(1)
  train.set_memory_limit('48G')

  with dsl.Condition(train.outputs['launch_server'] == 'true'):
    webapp = dsl.ContainerOp(
        name='webapp',
        image='gcr.io/google-samples/ml-pipeline-webapp-launcher:v3ap',
        arguments=["--model_name", 'ghsumm-%s' % (dsl.RUN_ID_PLACEHOLDER,),
            "--github_token", github_token]

        )
    webapp.after(serve)


if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(gh_summ, __file__ + '.tar.gz')
