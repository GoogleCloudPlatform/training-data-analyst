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

import os
import uuid
import logging
from threading import Timer

from flask import Flask, render_template, request
from mnist_client import get_prediction, random_mnist

app = Flask(__name__)


# handle requests to the server
@app.route("/")
def main():
  # get url parameters for HTML template
  name_arg = request.args.get('name', 'mnist-classifier')
  addr_arg = request.args.get('addr', 'ambassador')
  port_arg = request.args.get('port', '80')
  args = {"name": name_arg, "addr": addr_arg, "port": port_arg}
  logging.info(args)

  output = None
  connection = {"text": "", "success": False}
  img_id = str(uuid.uuid4())
  img_path = "static/tmp/" + img_id + ".png"
  try:
    # get a random test MNIST image
    x, y, _ = random_mnist(img_path)
    # get prediction from TensorFlow server
    pred = get_prediction(x, server_host=addr_arg, server_port=int(port_arg),
                          deployment_name=name_arg)
    # if no exceptions thrown, server connection was a success
    connection["text"] = "Connected to Seldon GRPC model serving service"
    connection["success"] = True
    # parse class confidence scores from server prediction
    scores_dict = []
    for i in range(0, 10):
      scores_dict += [{"index": str(i), "val": pred[i]}]
    output = {"truth": y,
              "img_path": img_path, "scores": scores_dict}
  except IOError as e:
    # server connection failed
    connection["text"] = "Could Not Connect to Server: " + str(e)
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
    logging.info("removed %s", path)
  except OSError:
    logging.error("no file at %s", path)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  app.run(debug=True, host='0.0.0.0')
