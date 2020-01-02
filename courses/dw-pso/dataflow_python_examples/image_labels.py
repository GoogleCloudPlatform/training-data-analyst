
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
image_labels.py is a Dataflow pipeline which reads a file
containing web urls or gcs references to image files and writes
the original file reference to a BigQuery table with the labels
identified by the Cloud Vision API.
"""

from __future__ import absolute_import
import argparse
import logging

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import vision
from google.cloud.vision import types

# Specify default parameters.
INPUT_FILE = 'gs://python-dataflow-example/data_files/image-list.txt'
BQ_DATASET = 'ImageLabelFlow'
BQ_TABLE = BQ_DATASET + '.dogs_short'


def detect_labels_uri(uri):
    """This Function detects labels in the image file located in Google Cloud Storage or on
    theWeb and returns a comma separated list of labels. This will return an empty string
    if not passed a valid image file

    Args:
        uri: a string link to a photo in gcs or on the web

    (Adapted From:
    https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/vision/cloud-client/detect/detect.py)
    """
    # Initialize cloud vision api client and image object.
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = uri

    # Send an api call for this image, extract label descriptions
    # and return a comma-space separated string.
    response = client.label_detection(image=image)
    labels = response.label_annotations
    label_list = [l.description for l in labels]
    return ', '.join(label_list)


class ImageLabeler(beam.DoFn):
    """
    This DoFn wraps the inner function detect_labels_uri to write a BigQuery row dictionary
    with the image file reference specified by the element from the prior PCollection and a list
    of labels for that image assigned by the Google Cloud Vision API.
    """

    def process(self, element, *args, **kwargs):
        """
        Args:
            element: A string specifying the uri of an image

        Returns:
            row: A list containing a dictionary defining a record to be written to BigQuery
        """
        labels_string = detect_labels_uri(element)

        return [{'image_location': element, 'labels': labels_string}]


def run(argv=None):
    """
    This funciton parses the command line arguments and runs the Beam Pipeline.

    Args:
        argv: list containing the commandline arguments for this call of the script.
    """
    parser = argparse.ArgumentParser()
    # Here we add some specific command line arguments we expect.
    # Specifically we have the input file to load and the output table to
    # This is the final stage of the pipeline, where we define the destination
    # of the data.  In this case we are writing to BigQuery.
    parser.add_argument(
        '--input', dest='input', required=False,
        help='Input file to read.  This can be a local file or '
             'a file in a Google Storage Bucket. However the image '
             'references shouldbe gcs links or web urls NOT local files',
        # This example file contains a total of only 3 lines specifying 3 image files in gcs.
        default=INPUT_FILE)

    # This defaults to the ImageLabelFlow dataset in my bigquery project.  You'll have
    # to create this dataset yourself using this command:
    # bq mk ImageLabelFlow
    parser.add_argument('--bq_table', dest='output', required=False,
                        help='Output BQ table to write results to.',
                        default=BQ_TABLE)

    # Parse arguments from the command line.
    known_args, pipeline_args = parser.parse_known_args(argv)

    # Initiate the pipeline using the pipeline arguments passed in from the
    # command line.  This includes information including where Dataflow should
    # store temp files, and what the project id is.
    p = beam.Pipeline(options=PipelineOptions(pipeline_args))

    (p
     # Read the file.  This is the source of the pipeline.  All further
     # processing starts with lines read from the file.  We use the input
     # argument from the command line.
     | 'Read from a File' >> beam.io.ReadFromText(known_args.input)
     # This stage of the pipeline translates from a CSV file single row
     # input specifying a gcs file, to a dictionary object consumable by BigQuery.
     # It refers to a function we have written that creates a row containing the image location
     # and the labels from the vision api.  This function will
     # be run in parallel on different workers using input from the
     # previous stage of the pipeline.
     | 'Vision API label_annotation wrapper' >> beam.ParDo(ImageLabeler())
     # This stage writes the data to the BigQuery table.
     | 'Write to BigQuery' >> beam.io.gcp.bigquery.WriteToBigQuery(
         # The table name is a required argument for the WriteToBigQuery io transform.
         # In this case we use the value passed in from the command line.
         known_args.output,
         # Here we use the simplest way of defining a schema:
         # fieldName:fieldType
         schema='image_location:STRING,labels:STRING',
         # Creates the table in BigQuery if it does not yet exist.
         create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
         # Append data to the output bq table.
         write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
         batch_size=500)
    )
    p.run().wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
