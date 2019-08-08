# -*- coding: utf-8 -*-

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import os

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask import url_for
import logging
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

credentials = GoogleCredentials.get_application_default()
api = discovery.build('ml', 'v1', credentials=credentials)

app = Flask(__name__)

project = os.getenv('PROJECT_ID', 'cloud-training-demos')
model_name = os.getenv('MODEL_NAME', 'poetry')
version_name = os.getenv('VERSION_NAME', 'v1')
problem_name = os.getenv('PROBLEM_NAME', 'poetry_line_problem')
t2t_usr_dir = os.getenv('T2T_USR_DIR', 'instance/poetry/trainer')
hparams_name = os.getenv('HPARAMS', 'transformer_poetry')
data_dir = os.getenv('DATADIR', 'gs://cloud-training-demos-ml/poetry/data')

def get_prediction(features):
  input_data = {'instances': [features]}
  parent = 'projects/%s/models/%s/versions/%s' % (project, model_name, version_name)
  prediction = api.projects().predict(body=input_data, name=parent).execute()
  return prediction


@app.route('/')
def index():
  return render_template('form.html')

@app.route('/form')
def input_form():
  return render_template('form.html')


@app.route('/api/predict', methods=['POST'])
def predict():
  data = json.loads(request.data.decode())
  features = {}
  tfrecord = encode_as_tfexample(data['first_line']).SerializeToString()
  features['input'] = {'b64': base64.b64encode(tfrecord)}
  prediction = get_prediction(features)
  decoded = decode( prediction['predictions'][0]['outputs'] )
  result = decoded.split('<EOS>')[0]
  return jsonify({'result': result})



# similar to T2T's query.py
# https://github.com/tensorflow/tensor2tensor/blob/master/tensor2tensor/serving/query.py
from tensor2tensor import problems as problems_lib  # pylint: disable=unused-import
from tensor2tensor.data_generators import text_encoder
from tensor2tensor.utils import registry
from tensor2tensor.utils import usr_dir
import tensorflow as tf

input_encoder = None
output_decoder = None
fname = None
def init():
   global input_encoder, output_decoder, fname
   tf.logging.set_verbosity(tf.logging.INFO)
   tf.logging.info("Trying to import poetry/trainer from {}".format(t2t_usr_dir))
   usr_dir.import_usr_dir(t2t_usr_dir)
   print(t2t_usr_dir)
   problem = registry.problem(problem_name)
   hparams = tf.contrib.training.HParams(data_dir=os.path.expanduser(data_dir))
   problem.get_hparams(hparams)
   fname = "inputs" if problem.has_inputs else "targets"
   input_encoder = problem.feature_info[fname].encoder
   output_decoder = problem.feature_info["targets"].encoder

def encode_as_tfexample(inputs):
   # read vocabulary once
   if input_encoder is None:
      init()

   # encode the input string
   input_ids = input_encoder.encode(inputs)
   input_ids.append(text_encoder.EOS_ID)
   
   # convert to TF Record
   features = {
     fname: tf.train.Feature(int64_list=tf.train.Int64List(value=input_ids))
   }
   return tf.train.Example(features=tf.train.Features(feature=features))

def decode(output_ids):
  return output_decoder.decode(output_ids)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
