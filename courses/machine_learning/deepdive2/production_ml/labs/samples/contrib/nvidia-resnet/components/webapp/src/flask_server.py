'''
Copyright 2018 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import logging
import os
# from threading import Timer

from flask import Flask, render_template, request
from trtis_client import get_prediction, random_image

app = Flask(__name__)

name_arg = os.getenv('MODEL_SERVE_NAME', 'resnet_graphdef')
addr_arg = os.getenv('TRTSERVER_HOST', '10.110.20.210')
port_arg = os.getenv('TRTSERVER_PORT', '8001')
model_version = os.getenv('MODEL_VERSION', '-1')

# handle requests to the server
@app.route("/")
def main():
  args = {"name": name_arg, "addr": addr_arg, "port": port_arg, "version": str(model_version)}
  logging.info("Request args: %s", args)

  output = None
  connection = {"text": "", "success": False}
  try:
    # get a random test MNIST image
    file_name, truth, serving_path = random_image('/workspace/web_server/static/images')
    # get prediction from TensorFlow server
    pred, scores = get_prediction(file_name,
                                  server_host=addr_arg,
                                  server_port=int(port_arg),
                                  model_name=name_arg,
                                  model_version=int(model_version))
    # if no exceptions thrown, server connection was a success
    connection["text"] = "Connected (model version: {0}".format(str(model_version))+ ")"
    connection["success"] = True
    # parse class confidence scores from server prediction
    output = {"truth": truth, "prediction": pred,
              "img_path": serving_path, "scores": scores}
  except Exception as e:  # pylint: disable=broad-except
    logging.info("Exception occured: %s", e)
    # server connection failed
    connection["text"] = "Exception making request: {0}".format(e)
  # after 10 seconds, delete cached image file from server
  # t = Timer(10.0, remove_resource, [img_path])
  # t.start()
  # render results using HTML template
  return render_template('index.html', output=output,
                         connection=connection, args=args)


def remove_resource(path):
  """
  attempt to delete file from path. Used to clean up MNIST testing images

  :param path: the path of the file to delete
  """
  try:
    os.remove(path)
    print("removed " + path)
  except OSError:
    print("no file at " + path)


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  logging.info("Starting flask.")
  app.run(debug=True, host='0.0.0.0', port=8080)
