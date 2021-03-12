# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# generate default secret name
import os
import kfp
from kfp import components
from kfp import dsl

secret_name = 'kfp-creds'
configuration_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/commons/config/component.yaml')
train_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/watson/train/component.yaml')
store_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/watson/store/component.yaml')
deploy_op = components.load_component_from_url('https://raw.githubusercontent.com/kubeflow/pipelines/master/components/ibm-components/watson/deploy/component.yaml')

# Helper function for secret mount and image pull policy
def use_ai_pipeline_params(secret_name, secret_volume_mount_path='/app/secrets', image_pull_policy='IfNotPresent'):
    def _use_ai_pipeline_params(task):
        from kubernetes import client as k8s_client
        task = task.add_volume(k8s_client.V1Volume(name=secret_name,  # secret_name as volume name
                                                   secret=k8s_client.V1SecretVolumeSource(secret_name=secret_name)))
        task.container.add_volume_mount(k8s_client.V1VolumeMount(mount_path=secret_volume_mount_path, 
                                                                 name=secret_name))
        task.container.set_image_pull_policy(image_pull_policy)
        return task
    return _use_ai_pipeline_params


# create pipelines

@dsl.pipeline(
    name='KFP on WML training',
    description='Kubeflow pipelines running on WML performing tensorflow image recognition.'
)
def kfp_wml_pipeline(
    GITHUB_TOKEN='',
    CONFIG_FILE_URL='https://raw.githubusercontent.com/user/repository/branch/creds.ini',
    train_code='tf-model.zip',
    execution_command='\'python3 convolutional_network.py --trainImagesFile ${DATA_DIR}/train-images-idx3-ubyte.gz --trainLabelsFile ${DATA_DIR}/train-labels-idx1-ubyte.gz --testImagesFile ${DATA_DIR}/t10k-images-idx3-ubyte.gz --testLabelsFile ${DATA_DIR}/t10k-labels-idx1-ubyte.gz --learningRate 0.001 --trainingIters 20000\'',
    framework='tensorflow',
    framework_version='1.15',
    runtime = 'python',
    runtime_version='3.6',
    run_definition = 'wml-tensorflow-definition',
    run_name = 'wml-tensorflow-run',
    model_name='wml-tensorflow-mnist',
    scoring_payload='tf-mnist-test-payload.json',
    compute_name='k80',
    compute_nodes='1'
):
    # op1 - this operation will create the credentials as secrets to be used by other operations
    get_configuration = configuration_op(
                   token=GITHUB_TOKEN,
                   url=CONFIG_FILE_URL,
                   name=secret_name
    )

    # op2 - this operation trains the model with the model codes and data saved in the cloud object store
    wml_train = train_op(
                   config=get_configuration.output,
                   train_code=train_code,
                   execution_command=execution_command,
                   framework=framework,
                   framework_version=framework_version,
                   runtime=runtime,
                   runtime_version=runtime_version,
                   run_definition=run_definition,
                   run_name=run_name,
                   compute_name=compute_name,
                   compute_nodes=compute_nodes
                   ).apply(use_ai_pipeline_params(secret_name, image_pull_policy='Always'))

    # op3 - this operation stores the model trained above
    wml_store = store_op(
                   wml_train.outputs['run_uid'],
                   model_name,
                   framework=framework,
                   framework_version=framework_version,
                   runtime_version=runtime_version
                   ).apply(use_ai_pipeline_params(secret_name, image_pull_policy='Always'))

    # op4 - this operation deploys the model to a web service and run scoring with the payload in the cloud object store
    wml_deploy = deploy_op(
                  wml_store.output,
                  model_name,
                  scoring_payload
                  ).apply(use_ai_pipeline_params(secret_name, image_pull_policy='Always'))

if __name__ == '__main__':
    # compile the pipeline
    import kfp.compiler as compiler
    pipeline_filename = kfp_wml_pipeline.__name__ + '.zip'
    compiler.Compiler().compile(kfp_wml_pipeline, pipeline_filename)
