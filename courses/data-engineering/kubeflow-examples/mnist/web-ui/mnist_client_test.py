"""Test mnist_client.

This file tests that we can send predictions to the model.

It is an integration test as it depends on having access to
a deployed model.

Python Path Requirements:
  kubeflow/testing/py - https://github.com/kubeflow/testing/tree/master/py
     * Provides utilities for testing

Manually running the test
 1. Configure your KUBECONFIG file to point to the desired cluster
 2. Use kubectl port-forward to forward a local port
    to the gRPC port of TFServing; e.g.
    kubectl -n ${NAMESPACE} port-forward service/mnist-service 9000:9000
"""

import os

from py import test_runner #pylint: disable=no-name-in-module

import mnist_client

from kubeflow.testing import test_util

class MnistClientTest(test_util.TestCase):
  def __init__(self, args):
    self.args = args
    super(MnistClientTest, self).__init__(class_name="MnistClientTest",
                                          name="MnistClientTest")

  def test_predict(self):  # pylint: disable=no-self-use
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir, "..", "data")
    img_path = os.path.abspath(data_dir)

    x, _, _ = mnist_client.random_mnist(img_path)

    server_host = "localhost"
    server_port = 9000
    model_name = "mnist"
    # get prediction from TensorFlow server
    pred, scores, _ = mnist_client.get_prediction(
      x, server_host=server_host, server_port=server_port,
      server_name=model_name, timeout=10)

    if pred < 0 or pred >= 10:
      raise ValueError("Prediction {0} is not in the range [0, 9]".format(pred))

    if len(scores) != 10:
      raise ValueError("Scores should have dimension 10. Got {0}".format(
        scores))
    # TODO(jlewi): Should we do any additional validation?

if __name__ == "__main__":
  test_runner.main(module=__name__)
