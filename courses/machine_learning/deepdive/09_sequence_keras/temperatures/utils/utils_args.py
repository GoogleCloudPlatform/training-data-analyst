# Copyright 2018 Google LLC
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

def read_args1(job_dir, data_dir):
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-dir', default=job_dir, help='GCS or local path where to store training checkpoints')
    parser.add_argument('--data-dir', default=data_dir, help='GCS or local path where to look for data files')
    args, other = parser.parse_known_args()
    return args.job_dir, args.data_dir