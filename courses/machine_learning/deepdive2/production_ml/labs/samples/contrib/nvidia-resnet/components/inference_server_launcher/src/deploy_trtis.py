# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
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

import argparse
import os
import logging
import subprocess
import requests


KUBEFLOW_NAMESPACE = 'kubeflow'
YAML_TEMPLATE = 'trtis-service-template.yaml'
YAML_FILE = 'trtis-service.yaml'


def main():
    parser = argparse.ArgumentParser(description='Inference server launcher')
    parser.add_argument('--trtserver_name', help='Name of trtis service')
    parser.add_argument('--model_path', help='...')

    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)
    logging.info('Generating TRTIS service template')

    template_file = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), YAML_TEMPLATE)
    target_file = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), YAML_FILE)

    with open(template_file, 'r') as template:
        with open(target_file, "w") as target:
            data = template.read()
            changed = data.replace('TRTSERVER_NAME', args.trtserver_name)
            changed1 = changed.replace(
                'KUBEFLOW_NAMESPACE', KUBEFLOW_NAMESPACE)
            changed2 = changed1.replace('MODEL_PATH', args.model_path)
            target.write(changed2)

    logging.info('Deploying TRTIS service')
    subprocess.call(['kubectl', 'apply', '-f', YAML_FILE])

    with open('/output.txt', 'w') as f:
        f.write(args.trtserver_name)
    

if __name__ == "__main__":
    main()
