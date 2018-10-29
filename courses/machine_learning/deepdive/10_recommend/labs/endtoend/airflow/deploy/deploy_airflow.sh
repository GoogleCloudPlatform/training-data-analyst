#!/bin/bash
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

# make a copy of the settings template and replace the project id
project_id=$(gcloud config get-value project 2> /dev/null)

< config/settings-template.yaml sed -E "s/YOUR-PROJECT-ID/${project_id}/g" > "config/settings.yaml"

# run deploy script
echo "python deploy_airflow.py --airflow_config config/airflow.cfg --settings config/settings.yaml --output_settings ./deployment-settings.yaml"
python deploy_airflow.py --airflow_config config/airflow.cfg \
  --settings config/settings.yaml \
  --output_settings ./deployment-settings.yaml

