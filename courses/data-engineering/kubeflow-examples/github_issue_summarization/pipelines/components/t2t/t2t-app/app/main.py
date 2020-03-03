# -*- coding: utf-8 -*-

# Copyright 2018 Google Inc.
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
import logging
import os
import random
import re
import requests

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import g, request

import pandas as pd

import tensorflow as tf


# similar to T2T's query.py
# https://github.com/tensorflow/tensor2tensor/blob/master/tensor2tensor/serving/query.py
from tensor2tensor import problems as problems_lib  # pylint: disable=unused-import
from tensor2tensor.utils import registry
from tensor2tensor.utils import usr_dir
from tensor2tensor.serving import serving_utils


app = Flask(__name__)

model_name = os.getenv('MODEL_NAME', 'ghsumm')
problem_name = os.getenv('PROBLEM_NAME', 'gh_problem')
t2t_usr_dir = os.getenv('T2T_USR_DIR', 'ghsumm/trainer')
hparams_name = os.getenv('HPARAMS', 'transformer_prepend')
data_dir = os.getenv('DATADIR', 'gs://aju-dev-demos-codelabs/kubecon/t2t_data_gh_all/')
github_token = os.getenv('GH_TOKEN', 'xxx')

SERVER = os.getenv('TFSERVING_HOST', 'ghsumm.kubeflow')
print("using server: %s" % SERVER)
SERVABLE_NAME = os.getenv('TF_SERVABLE_NAME', 'ghsumm')
print("using model servable name: %s" % SERVABLE_NAME)

SAMPLE_ISSUES = './github_issues_sample.csv'

SERVER_URL = 'http://' + SERVER + ':8500/v1/models/' + SERVABLE_NAME + ':predict'

def get_issue_body(issue_url):
  issue_url = re.sub('.*github.com/', 'https://api.github.com/repos/',
                     issue_url)
  tf.logging.info("issue url: %s", issue_url)
  # tf.logging.info("using GH token: %s", github_token)
  response = requests.get(
    issue_url, headers={
      'Authorization': 'token {}'.format(github_token)
    }).json()
  tf.logging.info("----response from url fetch: %s", response)
  return response['body']


@app.route('/')
def index():
  return render_template('index.html')

@app.route("/random_github_issue", methods=['GET'])
def random_github_issue():
  github_issues = getattr(g, '_github_issues', None)
  if github_issues is None:
    github_issues = g._github_issues = pd.read_csv(
      SAMPLE_ISSUES).body.tolist()
  random_issue = github_issues[random.randint(0,
                                 len(github_issues) - 1)]
  tf.logging.info("----random issue text: %s", random_issue)
  return jsonify({'body': random_issue})


@app.route("/summary", methods=['POST'])
def summary():
  """Main prediction route.

  Provides a machine-generated summary of the given text. Sends a request to a live
  model trained on GitHub issues.
  """
  global problem  #pylint: disable=global-statement
  if problem is None:
    init()
  request_fn = make_tfserving_rest_request_fn()

  if request.method == 'POST':
    issue_text = request.form["issue_text"]
    issue_url = request.form["issue_url"]
    if issue_url:
      print("fetching issue from URL...")
      issue_text = get_issue_body(issue_url)
    tf.logging.info("issue_text: %s", issue_text)
    outputs = serving_utils.predict([issue_text], problem, request_fn)
    outputs, = outputs
    output, score = outputs  #pylint: disable=unused-variable
    tf.logging.info("output: %s", output)

    return jsonify({'summary': output, 'body': issue_text})

  return ('', 204)

problem = None
def init():
  # global input_encoder, output_decoder, fname, problem
  global problem  #pylint: disable=global-statement
  tf.logging.set_verbosity(tf.logging.INFO)
  tf.logging.info("importing ghsumm/trainer from {}".format(t2t_usr_dir))
  usr_dir.import_usr_dir(t2t_usr_dir)
  print(t2t_usr_dir)
  problem = registry.problem(problem_name)
  hparams = tf.contrib.training.HParams(data_dir=os.path.expanduser(data_dir))
  problem.get_hparams(hparams)

def make_tfserving_rest_request_fn():
  """Wraps function to make CloudML Engine requests with runtime args."""

  def _make_tfserving_rest_request_fn(examples):
    """..."""
    # api = discovery.build("ml", "v1", credentials=credentials)
    # parent = "projects/%s/models/%s/versions/%s" % (cloud.default_project(),
                                                    # model_name, version)
    input_data = {
        "instances": [{
            "input": {
                "b64": base64.b64encode(ex.SerializeToString())
            }
        } for ex in examples]
    }

    response = requests.post(SERVER_URL, json=input_data)
    predictions = response.json()['predictions']
    tf.logging.info("Predictions: %s", predictions)
    return predictions

  return _make_tfserving_rest_request_fn

@app.errorhandler(500)
def server_error(e):
  logging.exception('An error occurred during a request.')
  return """
  An internal error occurred: <pre>{}</pre>
  See logs for full stacktrace.
  """.format(e), 500

if __name__ == '__main__':
  app.run(port=8080, debug=True)
