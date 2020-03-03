# Copyright 2019 Google Inc. All Rights Reserved.
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
from datetime import datetime
import logging
import retrying

from kubeflow.metadata import metadata #pylint: disable=no-name-in-module

DATASET = 'dataset'
MODEL = 'model'
METADATA_SERVICE = "metadata-service.kubeflow:8080"


def get_or_create_workspace(ws_name):
  return metadata.Workspace(
    # Connect to metadata-service in namesapce kubeflow in the k8s cluster.
    backend_url_prefix=METADATA_SERVICE,
    name=ws_name,
    description="a workspace for the GitHub summarization task",
    labels={"n1": "v1"})

def get_or_create_workspace_run(md_workspace, run_name):
  return metadata.Run(
    workspace=md_workspace,
    name=run_name,
    description="Metadata run for workflow %s" % run_name,
  )

@retrying.retry(stop_max_delay=180000)
def log_model_info(ws, ws_run, model_uri):
  exec2 = metadata.Execution(
      name="execution" + datetime.utcnow().isoformat("T"),
      workspace=ws,
      run=ws_run,
      description="train action",
  )
  _ = exec2.log_input(
      metadata.Model(
          description="t2t model",
          name="t2t-model",
          owner="amy@my-company.org",
          uri=model_uri,
          version="v1.0.0"
          ))

@retrying.retry(stop_max_delay=180000)
def log_dataset_info(ws, ws_run, data_uri):
  exec1 = metadata.Execution(
      name="execution" + datetime.utcnow().isoformat("T"),
      workspace=ws,
      run=ws_run,
      description="copy action",
  )
  _ = exec1.log_input(
      metadata.DataSet(
          description="gh summarization data",
          name="gh-summ-data",
          owner="amy@my-company.org",
          uri=data_uri,
          version="v1.0.0"
          ))


def main():
  parser = argparse.ArgumentParser(description='Serving webapp')
  parser.add_argument(
      '--log-type',
      help='...',
      required=True)
  parser.add_argument(
      '--workspace-name',
      help='...',
      required=True)
  parser.add_argument(
      '--run-name',
      help='...',
      required=True)
  parser.add_argument(
      '--data-uri',
      help='...',
      )
  parser.add_argument(
      '--model-uri',
      help='...',
      )

  parser.add_argument('--cluster', type=str,
                      help='GKE cluster set up for kubeflow. If set, zone must be provided. ' +
                           'If not set, assuming this runs in a GKE container and current ' +
                           'cluster is used.')
  parser.add_argument('--zone', type=str, help='zone of the kubeflow cluster.')
  args = parser.parse_args()

  ws = get_or_create_workspace(args.workspace_name)
  ws_run = get_or_create_workspace_run(ws, args.run_name)

  if args.log_type.lower() == DATASET:
    log_dataset_info(ws, ws_run, args.data_uri)
  elif args.log_type.lower() == MODEL:
    log_model_info(ws, ws_run, args.model_uri)
  else:
    logging.warning("Error: unknown metadata logging type %s", args.log_type)



if __name__ == "__main__":
  main()
