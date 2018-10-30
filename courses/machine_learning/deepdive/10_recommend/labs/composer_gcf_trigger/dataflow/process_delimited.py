# Copyright 2018 Google LLC
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

"""process_delimited.py is a Dataflow pipeline which reads a delimited file,
adds some additional metadata fields and loads the contents to a BigQuery table."""

from __future__ import absolute_import
import argparse
import logging
import ntpath
import re

import apache_beam as beam
from apache_beam.options import pipeline_options


class RowTransformer(object):
    """A helper class that contains utility methods to parse the delimited file
    and convert every record into a format acceptable to BigQuery. It also contains
    utility methods to add a load_dt and a filename fields as demonstration of
    how records can be enriched as part of the load process."""

    def __init__(self, delimiter, header, filename, load_dt):
        self.delimiter = delimiter

        # Extract the field name keys from the comma separated input.
        self.keys = re.split(',', header)

        self.filename = filename
        self.load_dt = load_dt

    def parse(self, row):
        """This method translates a single delimited record into a dictionary
        which can be loaded into BigQuery. It also adds filename and load_dt
        fields to the dictionary."""

        # Strip out the return characters and quote characters.
        values = re.split(self.delimiter, re.sub(r'[\r\n"]', '', row))

        row = dict(zip(self.keys, values))

        # Add an additional filename field.
        row['filename'] = self.filename

        # Add an additional load_dt field.
        row['load_dt'] = self.load_dt

        return row


def run(argv=None):
    """The main function which creates the pipeline and runs it."""
    parser = argparse.ArgumentParser()

    # Add the arguments needed for this specific Dataflow job.
    parser.add_argument(
        '--input', dest='input', required=True,
        help='Input file to read.  This can be a local file or '
             'a file in a Google Storage Bucket.')

    parser.add_argument('--output', dest='output', required=True,
                        help='Output BQ table to write results to.')

    parser.add_argument('--delimiter', dest='delimiter', required=False,
                        help='Delimiter to split input records.',
                        default=',')

    parser.add_argument('--fields', dest='fields', required=True,
                        help='Comma separated list of field names.')

    parser.add_argument('--load_dt', dest='load_dt', required=True,
                        help='Load date in YYYY-MM-DD format.')

    known_args, pipeline_args = parser.parse_known_args(argv)
    row_transformer = RowTransformer(delimiter=known_args.delimiter,
                                     header=known_args.fields,
                                     filename=ntpath.basename(known_args.input),
                                     load_dt=known_args.load_dt)

    p_opts = pipeline_options.PipelineOptions(pipeline_args)

    # Initiate the pipeline using the pipeline arguments passed in from the
    # command line.  This includes information including where Dataflow should
    # store temp files, and what the project id is.
    with beam.Pipeline(options=p_opts) as pipeline:
        # Read the file.  This is the source of the pipeline.  All further
        # processing starts with lines read from the file.  We use the input
        # argument from the command line.
        rows = pipeline | "Read from text file" >> beam.io.ReadFromText(known_args.input)

        # This stage of the pipeline translates from a delimited single row
        # input to a dictionary object consumable by BigQuery.
        # It refers to a function we have written.  This function will
        # be run in parallel on different workers using input from the
        # previous stage of the pipeline.
        dict_records = rows | "Convert to BigQuery row" >> beam.Map(
            lambda r: row_transformer.parse(r))

        # This stage of the pipeline writes the dictionary records into
        # an existing BigQuery table. The sink is also configured to truncate
        # the table if it contains any existing records.
        dict_records | "Write to BigQuery" >> beam.io.Write(
            beam.io.BigQuerySink(known_args.output,
                                 create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                                 write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
