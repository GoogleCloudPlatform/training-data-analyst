# Copyright 2018 Google Inc. All Rights Reserved.
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
import glob
import os
import re
import subprocess
from urlparse import urlparse

from google.cloud import storage


def copy_local_directory_to_gcs(project, local_path, bucket_name, gcs_path):
  """Recursively copy a directory of files to GCS.

  local_path should be a directory and not have a trailing slash.
  """
  assert os.path.isdir(local_path)
  for local_file in glob.glob(local_path + '/**'):
    if not os.path.isfile(local_file):
      continue
    remote_path = os.path.join(gcs_path, local_file[1 + len(local_path) :])
    storage_client = storage.Client(project=project)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(remote_path)
    blob.upload_from_filename(local_file)

def main():
  parser = argparse.ArgumentParser(description='ML Trainer')
  parser.add_argument(
      '--data-dir',
      help='...',
      required=True)
  parser.add_argument(
      '--project',
      help='...',
      required=True)

  args = parser.parse_args()

  problem = 'gh_problem'
  remote_data_dir = args.data_dir
  local_data_dir = '/ml/t2t_gh_data'
  local_source_data_file = '/ml/gh_data/github_issues.csv'

  data_copy_command1 = ['gsutil', 'cp',
      'gs://aju-dev-demos-codelabs/kubecon/gh_data/github_issues.csv',
      local_source_data_file
      ]
  print(data_copy_command1)
  result = subprocess.call(data_copy_command1)
  print(result)

  datagen_command = ['t2t-datagen', '--data_dir', local_data_dir, '--t2t_usr_dir',
      '/ml/ghsumm/trainer',
      '--problem', problem,
      '--tmp_dir', local_data_dir + '/tmp'
      ]
  print(datagen_command)
  result1 = subprocess.call(datagen_command)
  print(result1)

  print("copying processed input to %s" % remote_data_dir)
  o = urlparse(remote_data_dir)
  path = re.sub('^/', '', o.path)
  print("using bucket: %s and path: %s" % (o.netloc, path))
  copy_local_directory_to_gcs(args.project, local_data_dir, o.netloc, path)


if __name__ == "__main__":
  main()
