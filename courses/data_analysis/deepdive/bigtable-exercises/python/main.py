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

"""Demonstrates how to connect to Cloud Bigtable and run some basic operations.

Prerequisites:

- Create a Cloud Bigtable cluster.
  https://cloud.google.com/bigtable/docs/creating-cluster
- Set your Google Application Default Credentials.
  https://developers.google.com/identity/protocols/application-default-credentials
"""

import argparse

from google.cloud import bigtable


def main(project_id, instance_id, table_id):
    # [START connecting_to_bigtable]
    # The client must be created with admin=True because it will create a
    # table.
    client = bigtable.Client(project=project_id, admin=True)
    instance = client.instance(instance_id)
    # [END connecting_to_bigtable]

    # [START creating_a_table]
    print(('Creating the {} table.'.format(table_id)))
    table = instance.table(table_id)
    table.create()
    column_family_id = 'cf1'
    cf1 = table.column_family(column_family_id)
    cf1.create()
    # [END creating_a_table]

    # [START writing_rows]
    print('Writing some greetings to the table.')
    column_id = 'greeting'.encode('utf-8')
    greetings = [
        'Hello World!',
        'Hello Cloud Bigtable!',
        'Hello Python!',
    ]

    for i, value in enumerate(greetings):
        # Note: This example uses sequential numeric IDs for simplicity,
        # but this can result in poor performance in a production
        # application.  Since rows are stored in sorted order by key,
        # sequential keys can result in poor distribution of operations
        # across nodes.
        #
        # For more information about how to design a Bigtable schema for
        # the best performance, see the documentation:
        #
        #     https://cloud.google.com/bigtable/docs/schema-design
        row_key = 'greeting{}'.format(i)
        row = table.row(row_key)
        row.set_cell(
            column_family_id,
            column_id,
            value.encode('utf-8'))
        row.commit()
    # [END writing_rows]

    # [START getting_a_row]
    print('Getting a single greeting by row key.')
    key = 'greeting0'
    row = table.read_row(key.encode('utf-8'))
    value = row.cells[column_family_id][column_id][0].value
    print(('\t{}: {}'.format(key, value.decode('utf-8'))))
    # [END getting_a_row]

    # [START scanning_all_rows]
    print('Scanning for all greetings:')
    partial_rows = table.read_rows()
    partial_rows.consume_all()

    for row_key, row in list(partial_rows.rows.items()):
        key = row_key.decode('utf-8')
        cell = row.cells[column_family_id][column_id][0]
        value = cell.value.decode('utf-8')
        print(('\t{}: {}'.format(key, value)))
    # [END scanning_all_rows]

    # [START deleting_a_table]
    print(('Deleting the {} table.'.format(table_id)))
    table.delete()
    # [END deleting_a_table]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('project_id', help='Your Cloud Platform project ID.')
    parser.add_argument(
        'instance_id', help='ID of the Cloud Bigtable instance to connect to.')
    parser.add_argument(
        '--table',
        help='Table to create and destroy.',
        default='Hello-Bigtable')

    args = parser.parse_args()
    main(args.project_id, args.instance_id, args.table)
