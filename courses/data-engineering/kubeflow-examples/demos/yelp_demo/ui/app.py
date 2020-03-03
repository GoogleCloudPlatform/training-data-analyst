"""
Simple app that parses predictions from a trained model and displays them.
"""

import argparse
import base64
import logging
import requests
import tensorflow as tf
from flask import Flask, json, jsonify, render_template, request
from tensor2tensor.data_generators import text_encoder
from tensor2tensor.utils import registry


APP = Flask(__name__)

args = None
encoder = None

def get_encoder(data_dir):
  problem = registry.problem("yelp_sentiment")
  hparams = tf.contrib.training.HParams(data_dir=data_dir)
  problem.get_hparams(hparams)
  return problem.feature_info["inputs"].encoder


def encode_input(input_text):
  """
  Returns the b64 encoded serialized string.
  """
  input_int = encoder.encode(input_text)
  input_int.append(text_encoder.EOS_ID)

  # Needs a dummy "targets" field.
  features = {"inputs": tf.train.Feature(int64_list=tf.train.Int64List(value=input_int)),
              "targets": tf.train.Feature(int64_list=tf.train.Int64List(value=[0]))}
  example = tf.train.Example(features=tf.train.Features(feature=features))
  return base64.b64encode(example.SerializeToString()).decode("utf-8")

@APP.route("/kubeflow/predict", methods=['POST'])
def predict():
  """Main prediction route.
  """
  if request.method == 'POST':
    review_text = request.form["review_text"]
    encoded_review_text = str(encode_input(review_text))
    headers = {'content-type': 'application/json'}
    json_data = {"instances": [{"input": {"b64": encoded_review_text}}]}
    request_data = json.dumps(json_data)
    response = requests.post(
      url=args.model_url, headers=headers, data=request_data)
    return jsonify({"sentiment": json.loads(response.text)["predictions"][0]["outputs"][0][0][0]})

  return ('', 204)

@APP.route("/")
def index():
  """Default route.

  Placeholder, does nothing.
  """
  return render_template("index.html", title='Naive', mltype='naive')

@APP.route("/kubeflow")
def kubeflow():
  """Default route.

  Placeholder, does nothing.
  """
  return render_template("index.html", title='Kubeflow', mltype='kubeflow')



if __name__ == '__main__':
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--data_dir",
    default="gs://kubeflow-examples/t2t-yelp-data-40kvocab-2labels",
    type=str)
  parser.add_argument(
    "--model_url",
    default="http://serving:8000/model/serving:predict",
    type=str)
  parser.add_argument(
    "--port",
    default=80,
    type=int)
  args = parser.parse_args()
  logger.info("Creating encoder")
  encoder = get_encoder(args.data_dir)
  logger.info("Created encoder. Now serving the web app")
  APP.run(debug=True, host='0.0.0.0', port=args.port)
