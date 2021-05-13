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
"""Toy example demonstrating how to specify imagepullsecrets to access protected
container registry.
"""

import kfp
import kfp.dsl as dsl
from kubernetes import client as k8s_client


class GetFrequentWordOp(dsl.ContainerOp):
  """A get frequent word class representing a component in ML Pipelines.

  The class provides a nice interface to users by hiding details such as container,
  command, arguments.
  """
  def __init__(self, name, message):
    """Args:
         name: An identifier of the step which needs to be unique within a pipeline.
         message: a dsl.PipelineParam object representing an input message.
    """
    super(GetFrequentWordOp, self).__init__(
        name=name,
        image='python:3.5-jessie',
        command=['sh', '-c'],
        arguments=['python -c "from collections import Counter; '
                   'words = Counter(\'%s\'.split()); print(max(words, key=words.get))" '
                   '| tee /tmp/message.txt' % message],
        file_outputs={'word': '/tmp/message.txt'})

@dsl.pipeline(
  name='Save Most Frequent',
  description='Get Most Frequent Word and Save to GCS'
)
def save_most_frequent_word(message: str):
  """A pipeline function describing the orchestration of the workflow."""

  counter = GetFrequentWordOp(
          name='get-Frequent',
          message=message)
  # Call set_image_pull_secrets after get_pipeline_conf().
  dsl.get_pipeline_conf()\
    .set_image_pull_secrets([k8s_client.V1ObjectReference(name="secretA")])

if __name__ == '__main__':
  kfp.compiler.Compiler().compile(save_most_frequent_word, __file__ + '.yaml')
