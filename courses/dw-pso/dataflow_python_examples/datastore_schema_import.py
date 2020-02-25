# Copyright 2018 Google Inc.
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
"""Script to import file schema from CSV and save it into Google Cloud DataStore
To run this script, you will need Python packages listed in requirements.txt.
You can easily install them with virtualenv and pip by running these commands:
    virtualenv env
    source ./env/bin/activate
    pip install -r requirements.txt
    gcloud auth application-default login

This script's options and arguments are documented in
    python dataflow_python_examples/datastore_schema_import.py --help
Example to run the script:
python dataflow_import.py --schema-file=<path_to_file>
"""

import argparse
import collections
import csv
import json
import os

from google.cloud import datastore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema-file',
                        dest='schema_file',
                        required=True,
                        help='''
            File containing the schema of the input CSV data to be
            imported.
            Filename should be the same as the BQ table name that you
            want: "TABLENAME.csv".
            This file will be used to create a DataStore entity.
            Example:
                COLUMN_1,STRING
                COLUMN_2,FLOAT
            ''')
    args = parser.parse_args()
    client = datastore.Client()

    filename = args.schema_file
    print('Processing file %s' % filename)
    csvfile = open(filename, 'r')
    table = os.path.splitext(os.path.basename(filename))[0]
    filetext = csv.reader(csvfile, delimiter=',')
    fields = collections.OrderedDict()
    for rows in filetext:
        fields[rows[0]] = rows[1]
    key = client.key('Table', table)
    entry = datastore.Entity(key, exclude_from_indexes=['columns'])
    entry.update({"columns": unicode(json.dumps(fields), "utf-8")})
    client.put(entry)
    print('Created/Updated entry for table %s.' % table)
    print('Done.')


if __name__ == '__main__':
    main()
