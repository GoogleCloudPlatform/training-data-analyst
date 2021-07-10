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
from threading import Timer
import uuid

from flask import Flask, render_template, request
from mnist_client import get_prediction, random_mnist

app = Flask(__name__)


# handle requests to the server
@app.route("/")
def main():
  # get url parameters for HTML template
  name_arg = request.args.get('name', 'mnist')
  addr_arg = request.args.get('addr', 'mnist-service')
  port_arg = request.args.get('port', '9000')
  args = {"name": name_arg, "addr": addr_arg, "port": port_arg}
  logging.info("Request args: %s", args)

  output = None
  connection = {"text": "", "success": False}
  img_id = str(uuid.uuid4())
  img_path = "static/tmp/" + img_id + ".png"
  try:
    # get a random test MNIST image
    x, y, _ = random_mnist(img_path)
    # get prediction from TensorFlow server
    pred, scores, ver = get_prediction(x,
                                       server_host=addr_arg,
                                       server_port=int(port_arg),
                                       server_name=name_arg,
                                       timeout=10)
    # if no exceptions thrown, server connection was a success
    connection["text"] = "Connected (model version: " + str(ver) + ")"
    connection["success"] = True
    # parse class confidence scores from server prediction
    scores_dict = []
    for i in range(0, 10):
      scores_dict += [{"index": str(i), "val": scores[i]}]
    output = {"truth": y, "prediction": pred,
              "img_path": img_path, "scores": scores_dict}
  except Exception as e: # pylint: disable=broad-except
    logging.info("Exception occured: %s", e)
    # server connection failed
    connection["text"] = "Exception making request: {0}".format(e)
  # after 10 seconds, delete cached image file from server
  t = Timer(10.0, remove_resource, [img_path])
  t.start()
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
  app.run(debug=True, host='0.0.0.0')
