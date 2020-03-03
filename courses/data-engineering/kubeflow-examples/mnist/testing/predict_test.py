"""Test mnist_client.

This file tests that we can send predictions to the model
using REST.

It is an integration test as it depends on having access to
a deployed model.

We use the pytest framework because
  1. It can output results in junit format for prow/gubernator
  2. It has good support for configuring tests using command line arguments
     (https://docs.pytest.org/en/latest/example/simple.html)

Python Path Requirements:
  kubeflow/testing/py - https://github.com/kubeflow/testing/tree/master/py
     * Provides utilities for testing

Manually running the test
 1. Configure your KUBECONFIG file to point to the desired cluster
"""

import json
import logging
import os
import subprocess
import requests
from retrying import retry
import six

from kubernetes.config import kube_config
from kubernetes import client as k8s_client

import pytest

from kubeflow.testing import util

def is_retryable_result(r):
  if r.status_code == requests.codes.NOT_FOUND:
    message = "Request to {0} returned 404".format(r.url)
    logging.error(message)
    return True

  return False

@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000,
       stop_max_delay=5*60*1000,
       retry_on_result=is_retryable_result)
def send_request(*args, **kwargs):
  # We don't use util.run because that ends up including the access token
  # in the logs
  token = subprocess.check_output(["gcloud", "auth", "print-access-token"])
  if six.PY3 and hasattr(token, "decode"):
    token = token.decode()
  token = token.strip()

  headers = {
    "Authorization": "Bearer " + token,
  }

  if "headers" not in kwargs:
    kwargs["headers"] = {}

  kwargs["headers"].update(headers)

  r = requests.post(*args, **kwargs)

  return r

@pytest.mark.xfail
def test_predict(master, namespace, service):
  app_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
  if app_credentials:
    print("Activate service account")
    util.run(["gcloud", "auth", "activate-service-account",
              "--key-file=" + app_credentials])

  if not master:
    print("--master set; using kubeconfig")
    # util.load_kube_config appears to hang on python3
    kube_config.load_kube_config()
    api_client = k8s_client.ApiClient()
    host = api_client.configuration.host
    print("host={0}".format(host))
    master = host.rsplit("/", 1)[-1]

  this_dir = os.path.dirname(__file__)
  test_data = os.path.join(this_dir, "test_data", "instances.json")
  with open(test_data) as hf:
    instances = json.load(hf)

  # We proxy the request through the APIServer so that we can connect
  # from outside the cluster.
  url = ("https://{master}/api/v1/namespaces/{namespace}/services/{service}:8500"
         "/proxy/v1/models/mnist:predict").format(
           master=master, namespace=namespace, service=service)
  logging.info("Request: %s", url)
  r = send_request(url, json=instances, verify=False)

  if r.status_code != requests.codes.OK:
    msg = "Request to {0} exited with status code: {1} and content: {2}".format(
      url, r.status_code, r.content)
    logging.error(msg)
    raise RuntimeError(msg)

  content = r.content
  if six.PY3 and hasattr(content, "decode"):
    content = content.decode()
  result = json.loads(content)
  assert len(result["predictions"]) == 1
  predictions = result["predictions"][0]
  assert "classes" in predictions
  assert "predictions" in predictions
  assert len(predictions["predictions"]) == 10
  logging.info("URL %s returned; %s", url, content)

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  pytest.main()
