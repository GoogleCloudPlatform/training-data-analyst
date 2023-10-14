# Copyright 2023 Google LLC
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

import tensorflow as tf
from tensorflow import keras
import tensorflow_text
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.ml.inference.tensorflow_inference import TFModelHandlerTensor
from apache_beam.ml.inference.base import PredictionResult
from apache_beam.ml.inference.base import RunInference
from apache_beam.ml.inference.base import KeyedModelHandler
import argparse


class tag_with_key(beam.DoFn):
    # In this pardo, we key our elements using the attributes of the message
    def process(self, element):
        yield (element.attributes["userid"],(element.data).decode('UTF-8'))

class flag_for_toxic(beam.DoFn):
    def process(self, element):
        # Parsing the output of the inference
        # We need to pull out the tensor and conver it to numpy 
        # Note: for sake of brevity, we've used a hardcoded method
        # In production and for good practice you'll want to use the PredictionResult object
        tox_level = element[1][1].numpy().item()
        # We've put an arbitrary value to determine toxicity
        # This value is something you'll need to align with the model
        # The arbitrary value is just for demonstration purposes
        if tox_level > -0.5:
            yield ("not",element)
        else:
            yield ("nice",element)

def run(project_id, gaming_model_location, movie_model_location, pipeline_args):
    pipeline_options = PipelineOptions(
        pipeline_args, save_main_session=True)
    
    # We are using a topic for input
    # Pub/Sub IO will automatically create a subscription for us
    input_topic = "projects/{}/topics/tox-input".format(project_id)
    output_topic = "projects/{}/topics/tox-output".format(project_id)
    output_bigquery = "{}:demo.tox".format(project_id)

    with beam.Pipeline(options=pipeline_options) as p:

        # We first read from Pub/Sub
        # Because it's a streaming pipeline, we need to apply a window for the join
        # Finally we key the data so we can join it back after the A/B test
        # TODO: Follow Step 3: Create the pipeline to read from the input topic
        # TODO: Follow Step 4: Window the incoming element
        # TODO: Follow Step 5: Tag your element with the key

        # Load the model into a handler
        # We use KeyedModelHandler here to automatically handle the incoming keys
        # It also returns the key so you can preserve the key and use it after the prediction
        # TODO: Follow Step 6: Create the model handler

        # Use the handler to perform inference
        # Note that the gaming toxicity score is based on "toxic or not"
        # The scale differs from the movie model
        # TODO: Follow Step 7: Submit the input to the model for a result

        # Flag the values so we can determine if toxic or not
        # TODO: Apply the correct DoFn from above as instructed in Step 8: Parse your results from the prediction
        nice_or_not = (
            gaming_inference
            | beam.ParDo( # Put the right DoFn here )
        )

        # Print to screen so we can see the results
        # TODO: Follow Step 9: Do a simple MAP and print

        # Filter, if toxic then write to Pub/Sub
        # "Not" denotes not nice
        # TODO: Follow Step 10: Filter your data on the result key

        # Write to Pub/Sub
        # TODO: Follow Step 11: Submit the messages to Pub/Sub for further action

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project_id',
        dest='project_id',
        required=True,
        help=('project id'))
    parser.add_argument(
        '--gaming',
        dest='gaming_loc',
        required=True,
        help=('location of gaming model'))
    parser.add_argument(
        '--movie',
        dest='movie_loc',
        required=True,
        help=('location of movie model'))
    known_args, pipeline_args = parser.parse_known_args()
    run(known_args.project_id, known_args.gaming_loc, known_args.movie_loc, pipeline_args)

