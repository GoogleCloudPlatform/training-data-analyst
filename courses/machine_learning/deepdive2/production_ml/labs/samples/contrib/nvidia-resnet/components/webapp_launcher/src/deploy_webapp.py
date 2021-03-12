# Copyright 2018 Google Inc. All Rights Reserved.
# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import logging
import subprocess
import requests


KUBEFLOW_NAMESPACE = 'kubeflow'
YAML_TEMPLATE = 'webapp-service-template.yaml'
YAML_FILE = 'webapp-service.yaml'


def main():
    parser = argparse.ArgumentParser(description='Webapp launcher')
    parser.add_argument('--trtserver_name', help='Name of trtis service')
    parser.add_argument('--workflow_name', help='Workflow name')
    parser.add_argument('--model_name', help='Name of default model')
    parser.add_argument('--model_version', help='Model version')
    parser.add_argument('--webapp_prefix',
                        help='Webapp prefix as subpath of Kubeflow UI')
    parser.add_argument(
        '--webapp_port', help='Webapp port inside the Kubernetes cluster')

    args = parser.parse_args()

    print("using model name: %s and namespace: %s" %
          (args.model_name, KUBEFLOW_NAMESPACE))

    logging.getLogger().setLevel(logging.INFO)
    logging.info('Generating webapp service template')

    template_file = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), YAML_TEMPLATE)
    target_file = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), YAML_FILE)

    with open(template_file, 'r') as template:
        with open(target_file, "w") as target:
            data = template.read()
            changed = data.replace('MODEL_PASSIN_NAME', args.model_name)
            changed1 = changed.replace(
                'KUBEFLOW_NAMESPACE', KUBEFLOW_NAMESPACE)
            changed2 = changed1.replace(
                'MODEL_PASSIN_VERSION', args.model_version)
            changed3 = changed2.replace('TRTSERVER_NAME', args.trtserver_name)
            changed4 = changed3.replace('WORKFLOW_NAME', args.workflow_name)
            changed5 = changed4.replace('WEBAPP_PREFIX', args.webapp_prefix)
            changed6 = changed5.replace('WEBAPP_PORT', args.webapp_port)
            target.write(changed6)

    subprocess.call(['kubectl', 'apply', '-f', YAML_FILE])
    logging.info('Deploying webapp service')


if __name__ == "__main__":
    main()
