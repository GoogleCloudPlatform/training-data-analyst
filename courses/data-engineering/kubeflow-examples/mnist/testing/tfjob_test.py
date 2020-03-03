"""Test training using TFJob.

This file tests that we can submit the job
and that the job runs to completion.

It is an integration test as it depends on having access to
a Kubeflow deployment to submit the TFJob to.

Python Path Requirements:
  kubeflow/tf-operator/py - https://github.com/kubeflow/tf-operator
     * Provides utilities for testing TFJobs
  kubeflow/testing/py - https://github.com/kubeflow/testing/tree/master/py
     * Provides utilities for testing

Manually running the test
  pytest tfjobs_test.py \
    tfjob_name=tfjobs-test-${BUILD_ID} \
    namespace=${test_namespace} \
    trainer_image=${trainning_image} \
    train_steps=10 \
    batch_size=10 \
    learning_rate=0.01 \
    num_ps=1 \
    num_workers=2 \
    model_dir=${model_dir} \
    export_dir=${model_dir} \
"""

import json
import logging
import os
import pytest

from kubernetes.config import kube_config
from kubernetes import client as k8s_client
from kubeflow.tf_operator import tf_job_client #pylint: disable=no-name-in-module

from kubeflow.testing import util

def test_training(record_xml_attribute, tfjob_name, namespace, trainer_image, num_ps, #pylint: disable=too-many-arguments
                  num_workers, train_steps, batch_size, learning_rate, model_dir, export_dir):

  util.set_pytest_junit(record_xml_attribute, "test_mnist")

  util.maybe_activate_service_account()

  app_dir = os.path.join(os.path.dirname(__file__), "../training/GCS")
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

  # Configurate custom parameters using kustomize
  util.run(['kustomize', 'edit', 'set', 'namespace', namespace], cwd=app_dir)
  util.run(['kustomize', 'edit', 'set', 'image', 'training-image=' + trainer_image], cwd=app_dir)

  util.run(['../base/definition.sh', '--numPs', num_ps], cwd=app_dir)
  util.run(['../base/definition.sh', '--numWorkers', num_workers], cwd=app_dir)

  trainning_config = {
    "name": tfjob_name,
    "trainSteps": train_steps,
    "batchSize": batch_size,
    "learningRate": learning_rate,
    "modelDir": model_dir,
    "exportDir": export_dir,
  }

  configmap = 'mnist-map-training'
  for key, value in trainning_config.items():
    util.run(['kustomize', 'edit', 'add', 'configmap', configmap,
            '--from-literal=' + key + '=' + value], cwd=app_dir)

  # Created the TFJobs.
  util.run(['kustomize', 'build', app_dir, '-o', 'generated.yaml'], cwd=app_dir)
  util.run(['kubectl', 'apply', '-f', 'generated.yaml'], cwd=app_dir)
  logging.info("Created job %s in namespaces %s", tfjob_name, namespace)

  kube_config.load_kube_config()
  api_client = k8s_client.ApiClient()

  # Wait for the job to complete.
  logging.info("Waiting for job to finish.")
  results = tf_job_client.wait_for_job(
        api_client,
        namespace,
        tfjob_name,
        status_callback=tf_job_client.log_status)
  logging.info("Final TFJob:\n %s", json.dumps(results, indent=2))

  # Check for errors creating pods and services. Can potentially
  # help debug failed test runs.
  creation_failures = tf_job_client.get_creation_failures_from_tfjob(
      api_client, namespace, results)
  if creation_failures:
    logging.warning(creation_failures)

  if not tf_job_client.job_succeeded(results):
    failure = "Job {0} in namespace {1} in status {2}".format(  # pylint: disable=attribute-defined-outside-init
        tfjob_name, namespace, results.get("status", {}))
    logging.error(failure)

    # if the TFJob failed, print out the pod logs for debugging.
    pod_names = tf_job_client.get_pod_names(
        api_client, namespace, tfjob_name)
    logging.info("The Pods name:\n %s", pod_names)

    core_api = k8s_client.CoreV1Api(api_client)

    for pod in pod_names:
      logging.info("Getting logs of Pod %s.", pod)
      try:
        pod_logs = core_api.read_namespaced_pod_log(pod, namespace)
        logging.info("The logs of Pod %s log:\n %s", pod, pod_logs)
      except k8s_client.rest.ApiException as e:
        logging.info("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n", e)
    return

  # We don't delete the jobs. We rely on TTLSecondsAfterFinished
  # to delete old jobs. Leaving jobs around should make it
  # easier to debug.

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  pytest.main()
