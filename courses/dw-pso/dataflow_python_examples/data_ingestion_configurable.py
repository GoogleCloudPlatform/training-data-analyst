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
"""Dataflow pipeline that reads 1-n files, transforms their content, and writes
it to BigQuery tables using schema information stored in DataStore.

To run this script, you will need Python packages listed in requirements.txt.

You can easily install them with virtualenv and pip by running these commands:

    virtualenv env
    source ./env/bin/activate
    pip install -r requirements.txt

To get documentation on the script options run:
    python dataflow_python_examples/data_ingestion_configurable.py --help
"""

import argparse
import json
import logging
import os

import apache_beam as beam

from collections import OrderedDict

from apache_beam.io.gcp.internal.clients.bigquery import (TableSchema,
                                                          TableFieldSchema)
from google.api_core.exceptions import InvalidArgument
from google.auth.exceptions import GoogleAuthError
from google.cloud import datastore


class FileCoder(object):
    """Encode and decode CSV data coming from the files."""
    def __init__(self, columns):
        self._columns = columns
        self._num_columns = len(columns)
        self._delimiter = ","

    def encode(self, value):
        import csv
        import StringIO
        st = StringIO.StringIO()
        cw = csv.writer(os,
                        delimiter=self._delimiter,
                        quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
        cw.writerow(value.values())
        return st.getvalue().strip('\r\n')

    def decode(self, value):
        import csv
        split_value = list(csv.reader([value], delimiter=self._delimiter))[0]

        if len(split_value) != self._num_columns:
            logging.warn('Record length %s, expected %s: [%s]' %
                         (len(split_value), self._num_columns, split_value))
            return []
        return dict((self._columns[i], v) for i, v in enumerate(split_value))


class PrepareFieldTypes(beam.DoFn):
    def __init__(self, encoding='utf-8', time_format='%Y-%m-%d %H:%M:%S %Z'):
        import importlib
        self._encoding = encoding
        # Additional time format to use in case the default one does not work
        self._time_format = [time_format, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
        self._tm = importlib.import_module('time')

    def _return_default_value(self, ftype):
        if ftype == 'INTEGER':
            return 0
        elif ftype == 'FLOAT':
            return 0
        elif ftype == 'DATATIME':
            return self._tm.mktime(self._tm.strptime('1970-01-01', '%Y-%m-%d'))
        elif ftype == 'TIMESTAMP':
            return 0
        else:
            return ''

    def process(self, element, fields):
        if not hasattr(element, '__len__'):
            logging.warn('Element %s has no length' % element)
            return []
        if len(element) != len(fields):
            logging.warn('Row has %s elements instead of %s' %
                         (len(element), len(fields)))
            return []
        for k, v in element.items():
            ftype = fields[k]
            try:
                if not v:
                    v = self._return_default_value(ftype)
                elif ftype == 'STRING':
                    if isinstance(v, str):
                        v = v.decode(self._encoding, errors='ignore')
                elif ftype == 'INTEGER':
                    v = int(v)
                elif ftype == 'FLOAT':
                    v = float(v)
                elif ftype == 'DATETIME':
                    try:
                        v = self._tm.mktime(
                            self._tm.strptime(v, self._time_format))
                    except (ValueError, TypeError), e:
                        logging.warn('Cannot convert type %s for element %s: '
                                     '%s. Returning default value.' %
                                     (ftype, v, e))
                        v = self._return_default_value(ftype)

                elif ftype == 'TIMESTAMP':
                    for fmt in (self._time_format):
                        try:
                            v = int(self._tm.mktime(self._tm.strptime(v, fmt)))
                        except ValueError, e:
                            pass
                        else:
                            break
                    if not isinstance(v, int):
                        logging.warn('Cannot convert date %s. Error: %s' %
                                     (v, e))
                        v = self._return_default_value(ftype)
                else:
                    logging.warn('Unknown field type %s' % ftype)
                    v = self._return_default_value(ftype)
            except (TypeError, ValueError), e:
                logging.warn('Cannot convert type %s for element %s: '
                             '%s. Returning default value.' % (ftype, v, e))
                v = self._return_default_value(ftype)
            element[k] = v
        return [element]


class InjectTimestamp(beam.DoFn):
    def process(self, element):
        import time
        element['_RAWTIMESTAMP'] = int(time.mktime(time.gmtime()))
        return [element]


def _fetch_table(table_name):
    try:
        client = datastore.Client()
    except GoogleAuthError:
        # TODO(lcaggioni.ludomagno): fail gracefully
        pass
    return client.get(client.key('Table', table_name))


def _get_bq_schema(fields):
    bq_fields = []
    for k, v in fields.items():
        bq_fields.append(
            TableFieldSchema(name=k, type=v, description='Field %s' % k))
    bq_fields.append(
        TableFieldSchema(name='_RAWTIMESTAMP',
                         type='TIMESTAMP',
                         description='Injected timestamp'))
    return TableSchema(fields=bq_fields)


def run(argv=None):
    """The main function which creates the pipeline and runs it"""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input-bucket',
        dest='input_bucket',
        required=True,
        default='data-daimlr',
        help='GS bucket_name where the input files are present')
    parser.add_argument(
        '--input-path',
        dest='input_path',
        required=False,
        help='GS folder name, if the input files are inside a bucket folder')
    parser.add_argument(
        '--input-files',
        dest='input_files',
        required=True,
        help='Comma delimited names of all input files to be imported')
    parser.add_argument(
        '--bq-dataset',
        dest='bq_dataset',
        required=True,
        default='rawdata',
        help='Output BQ dataset to write the results to')

    # Parse arguments from the command line
    known_args, pipeline_args = parser.parse_known_args(argv)

    # Initiate the pipeline using the pipeline arguments
    logging.info('START - Pipeline')
    p = beam.Pipeline(argv=pipeline_args)

    for input_file in known_args.input_files.split(','):
        logging.info('START - Preparing file %s' % (input_file))

        table_name = os.path.splitext(input_file)[0].split('_')[0]
        logging.info('Retrieving information for table %s' % (table_name))

        try:
            table = _fetch_table(table_name)
        except InvalidArgument, e:
            raise SystemExit('Error getting information for table [%s]: %s' %
                             (table_name, e))
        if not table:
            raise SystemExit('No table found')

        fields = json.loads(table['columns'].decode('utf-8'),
                            object_pairs_hook=OrderedDict)
        gs_path = os.path.join(
            known_args.input_bucket, *[
                known_args.input_path if known_args.input_path else "",
                input_file
            ])
        logging.info('GS path being read from: %s' % (gs_path))

        (p
         | 'Read From Text - ' + input_file >> beam.io.ReadFromText(
             gs_path, coder=FileCoder(fields.keys()), skip_header_lines=1)
         | 'Prepare Field Types - ' + input_file >> beam.ParDo(
             PrepareFieldTypes(), fields)
         | 'Inject Timestamp - ' + input_file >> beam.ParDo(InjectTimestamp())
         | 'Write to BigQuery - ' + input_file >> beam.io.Write(
             beam.io.BigQuerySink(
                 # The table name passed in from the command line
                 known_args.bq_dataset + '.' + table_name,
                 # Schema of the table
                 schema=_get_bq_schema(fields),
                 # Creates the table in BigQuery if it does not exist
                 create_disposition=beam.io.BigQueryDisposition.
                 CREATE_IF_NEEDED,
                 # Data will be appended to the table
                 write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)))
        logging.info('END - Preparing file %s' % (input_file))

    p.run().wait_until_finish()
    logging.info('END - Pipeline')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
