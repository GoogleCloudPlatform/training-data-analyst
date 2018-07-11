#!/usr/bin/env python

# Copyright 2016 Google Inc.
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

"""
Read from our rollups data and print every time minute-over-minute
transaction volume drops more than 50%.
"""

import argparse

from google.cloud import bigtable


def main(project_id, instance_id, table_id):
  client = bigtable.Client(project=project_id)
  instance = client.instance(instance_id)

  table = instance.table(table_id)

  partial_rows = table.read_rows(start_key="hourly")
  partial_rows.consume_all()

  #for row_key, row in partial_rows.rows.items():
    # TODO: Print a message if there is a > 50% drop minute over minute.
    # Remember our data model: each row has a single column the "rollups"
    # family with a name of empty string (""). There is one cell per minute
    # that contains the # of actions in that minute.
    # Documentation on the way Python exposes this is here:
    # https://googlecloudplatform.github.io/google-cloud-python/latest/bigtable/data-api.html


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description=__doc__,
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('project_id', help='Your Cloud Platform project ID.')
  parser.add_argument(
      'instance_id', help='ID of the Cloud Bigtable instance to connect to.')
  parser.add_argument(
      'table',
      help='Table from previous exercises')

  args = parser.parse_args()
  main(args.project_id, args.instance_id, args.table)
