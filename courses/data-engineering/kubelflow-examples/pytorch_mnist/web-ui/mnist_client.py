#!/usr/bin/env python2.7
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

from __future__ import print_function

import logging
import grpc
import numpy as np
from PIL import Image
from tensorflow.examples.tutorials.mnist import input_data
from proto import prediction_pb2
from proto import prediction_pb2_grpc


def get_prediction(image, server_host='127.0.0.1', server_port=8080,
                   deployment_name="server"):
  """
  Retrieve a prediction from a TensorFlow model server

  :param image:       a MNIST image represented as a 1x784 array
  :param server_host: the address of the Seldon server
  :param server_port: the port used by the server
  :param deployment_name: the name of the deployment
  :return 0:          the integer predicted in the MNIST image
  """

  try:
    # build request
    chosen = 0
    data = image[chosen].reshape(784)
    datadef = prediction_pb2.DefaultData(
      tensor=prediction_pb2.Tensor(
        shape=data.shape,
        values=data
      )
    )

    # retrieve results
    request = prediction_pb2.SeldonMessage(data=datadef)
    logging.info("connecting to:%s:%i", server_host, server_port)
    channel = grpc.insecure_channel(server_host + ":" + str(server_port))
    stub = prediction_pb2_grpc.SeldonStub(channel)
    metadata = [('seldon', deployment_name)]
    response = stub.Predict(request=request, metadata=metadata)
  except IOError as e:
    # server connection failed
    logging.error("Could Not Connect to Server: %s", str(e))
  return response.data.tensor.values


def random_mnist(save_path=None):
  """
  Pull a random image out of the MNIST test dataset
  Optionally save the selected image as a file to disk

  :param save_path: the path to save the file to. If None, file is not saved
  :return 0: a 1x784 representation of the MNIST image
  :return 1: the ground truth label associated with the image
  :return 2: a bool representing whether the image file was saved to disk
  """

  mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)
  batch_size = 1
  batch_x, batch_y = mnist.test.next_batch(batch_size)

  saved = False
  if save_path is not None:
    # save image file to disk
    try:
      data = (batch_x * 255).astype(np.uint8).reshape(28, 28)
      img = Image.fromarray(data, 'L')
      img.save(save_path)
      saved = True
    except IOError:
      pass
  return batch_x, np.argmax(batch_y), saved
