"""
Simple app that parses predictions from a trained model and displays them.
"""

import argparse
import logging
import os
import re
import random
import sys

import requests
import pandas as pd
from flask import Flask, json, render_template, request, g, jsonify

APP = Flask(__name__)
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
SAMPLE_DATA_URL = ('https://storage.googleapis.com/kubeflow-examples/'
                   'github-issue-summarization-data/github_issues_sample.csv')


def get_issue_body(issue_url):
  issue_url = re.sub('.*github.com/', 'https://api.github.com/repos/',
                     issue_url)
  return requests.get(
    issue_url, headers={
      'Authorization': 'token {}'.format(GITHUB_TOKEN)
    }).json()['body']


@APP.route("/")
def index():
  """Default route.

  Placeholder, does nothing.
  """
  return render_template("index.html")


@APP.route("/summary", methods=['POST'])
def summary():
  """Main prediction route.

  Provides a machine-generated summary of the given text. Sends a request to a live
  model trained on GitHub issues.
  """
  if request.method == 'POST':
    issue_text = request.form["issue_text"]
    issue_url = request.form["issue_url"]
    if issue_url:
      issue_text = get_issue_body(issue_url)
    headers = {'content-type': 'application/json'}
    json_data = {"data": {"ndarray": [[issue_text]]}}
    response = requests.post(
      url=args.model_url, headers=headers, data=json.dumps(json_data))
    response_json = json.loads(response.text)
    issue_summary = response_json["data"]["ndarray"][0][0]
    return jsonify({'summary': issue_summary, 'body': issue_text})

  return ('', 204)


@APP.route("/random_github_issue", methods=['GET'])
def random_github_issue():
  github_issues = getattr(g, '_github_issues', None)
  if github_issues is None:
    github_issues = g._github_issues = pd.read_csv(
      SAMPLE_DATA_URL).body.tolist()
  return jsonify({
    'body':
    github_issues[random.randint(0,
                                 len(github_issues) - 1)]
  })


if __name__ == '__main__':
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--model_url",
    default="http://issue-summarization.kubeflow.svc.cluster.local:8000/api/v0.1/predictions",
    type=str)
  parser.add_argument(
    "--port",
    default=80,
    type=int)
  args = parser.parse_args()
  # Use print not logging because logging buffers the output and there's
  # no way to force a flush.
  print("Serving the web app")
  print("Using model_url {0}".format(args.model_url))
  sys.stdout.flush()
  APP.run(debug=True, host='0.0.0.0', port=args.port)
