"""Test deploying the mnist model.

This file tests that we can deploy the model.

It is an integration test as it depends on having access to
a Kubeflow deployment to deploy on. It also depends on having a model.

Python Path Requirements:
  kubeflow/testing/py - https://github.com/kubeflow/testing/tree/master/py
     * Provides utilities for testing

Manually running the test
  pytest deploy_test.py \
    name=mnist-deploy-test-${BUILD_ID} \
    namespace=${namespace} \
    modelBasePath=${modelDir} \
    exportDir=${modelDir} \

"""

import logging
import os
import pytest

from kubernetes.config import kube_config
from kubernetes import client as k8s_client

from kubeflow.testing import util


def test_deploy(record_xml_attribute, deploy_name, namespace, model_dir, export_dir):

  util.set_pytest_junit(record_xml_attribute, "test_deploy")

  util.maybe_activate_service_account()

  app_dir = os.path.join(os.path.dirname(__file__), "../serving/GCS")
  app_dir = os.path.abspath(app_dir)
  logging.info("--app_dir not set defaulting to: %s", app_dir)

  # TODO (@jinchihe) Using kustomize 2.0.3 to work around below issue:
  # https://github.com/kubernetes-sigs/kustomize/issues/1295
  kusUrl = 'https://github.com/kubernetes-sigs/kustomize/' \
           'releases/download/v2.0.3/kustomize_2.0.3_linux_amd64'
  util.run(['wget', '-q', '-O', '/usr/local/bin/kustomize', kusUrl], cwd=app_dir)
  util.run(['chmod', 'a+x', '/usr/local/bin/kustomize'], cwd=app_dir)

  # TODO (@jinchihe): The kubectl need to be upgraded to 1.14.0 due to below issue.
  # Invalid object doesn't have additional properties ...
  kusUrl = 'https://storage.googleapis.com/kubernetes-release/' \
           'release/v1.14.0/bin/linux/amd64/kubectl'
  util.run(['wget', '-q', '-O', '/usr/local/bin/kubectl', kusUrl], cwd=app_dir)
  util.run(['chmod', 'a+x', '/usr/local/bin/kubectl'], cwd=app_dir)

  # Configure custom parameters using kustomize
  configmap = 'mnist-map-serving'
  util.run(['kustomize', 'edit', 'set', 'namespace', namespace], cwd=app_dir)
  util.run(['kustomize', 'edit', 'add', 'configmap', configmap,
           '--from-literal=name' + '=' + deploy_name], cwd=app_dir)

  util.run(['kustomize', 'edit', 'add', 'configmap', configmap,
            '--from-literal=modelBasePath=' + model_dir], cwd=app_dir)
  util.run(['kustomize', 'edit', 'add', 'configmap', configmap,
            '--from-literal=exportDir=' + export_dir], cwd=app_dir)

  # Apply the components
  util.run(['kustomize', 'build', app_dir, '-o', 'generated.yaml'], cwd=app_dir)
  util.run(['kubectl', 'apply', '-f', 'generated.yaml'], cwd=app_dir)

  kube_config.load_kube_config()
  api_client = k8s_client.ApiClient()
  util.wait_for_deployment(api_client, namespace, deploy_name, timeout_minutes=4)

  # We don't delete the resources. We depend on the namespace being
  # garbage collected.

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  pytest.main()
