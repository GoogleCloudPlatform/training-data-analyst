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

  all_cells = []
  for row_key, row in list(partial_rows.rows.items()):
    for cell in row.cells[b'rollups']['']:
      all_cells.append(cell)

  last_cell = None
  for cell in all_cells:
    if last_cell and int(last_cell.value) / 2 > int(cell.value):
      print("Big drop from {} to {} between {} and {}".format(last_cell.value,
                                                              cell.value,
                                                              last_cell.timestamp,
                                                              cell.timestamp))
    last_cell = cell


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
