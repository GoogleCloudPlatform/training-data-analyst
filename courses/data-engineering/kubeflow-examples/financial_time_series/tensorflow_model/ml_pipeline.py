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
import kfp.gcp as gcp


class Preprocess(dsl.ContainerOp):

  def __init__(self, name, bucket, cutoff_year):
    super(Preprocess, self).__init__(
      name=name,
      # image needs to be a compile-time string
      image='gcr.io/<project>/<image-name>/cpu:v1',
      command=['python3', 'run_preprocess.py'],
      arguments=[
        '--bucket', bucket,
        '--cutoff_year', cutoff_year,
        '--kfp'
      ],
      file_outputs={'blob-path': '/blob_path.txt'}
    )


class Train(dsl.ContainerOp):

  def __init__(self, name, blob_path, tag, bucket, model):
    super(Train, self).__init__(
      name=name,
      # image needs to be a compile-time string
      image='gcr.io/<project>/<image-name>/cpu:v1',
      command=['python3', 'run_train.py'],
      arguments=[
        '--tag', tag,
        '--blob_path', blob_path,
        '--bucket', bucket,
        '--model', model,
        '--kfp'
      ],
      file_outputs={'mlpipeline_metrics': '/mlpipeline-metrics.json',
                    'accuracy': '/tmp/accuracy'}
    )


class Deploy(dsl.ContainerOp):

  def __init__(self, name, tag, bucket):
    super(Deploy, self).__init__(
      name=name,
      # image needs to be a compile-time string
      image='gcr.io/<project>/<image-name>/cpu:v1',
      command=['python3', 'run_deploy.py'],
      arguments=[
        '--tag', tag,
        '--bucket', bucket,
      ],
    )


@dsl.pipeline(
  name='financial time series',
  description='Train Financial Time Series'
)
def preprocess_train_deploy(
        bucket: str = '<bucket>',
        cutoff_year: str = '2010',
        tag: str = '4',
        model: str = 'DeepModel'
):
  """Pipeline to train financial time series model"""
  preprocess_op = Preprocess('preprocess', bucket, cutoff_year).apply(
    gcp.use_gcp_secret('user-gcp-sa'))
  #pylint: disable=unused-variable
  train_op = Train('train', preprocess_op.output, tag,
                   bucket, model).apply(gcp.use_gcp_secret('user-gcp-sa'))
  with dsl.Condition(train_op.outputs['accuracy'] > 0.7):
    deploy_op = Deploy('deploy', tag, bucket).apply(gcp.use_gcp_secret('user-gcp-sa'))


if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(preprocess_train_deploy, __file__ + '.tar.gz')
