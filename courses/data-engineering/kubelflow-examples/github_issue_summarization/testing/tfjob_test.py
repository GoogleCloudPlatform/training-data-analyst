"""Test training using TFJob.

This file tests that we can submit the job from ksonnet
and that the job runs to completion.

It is an integration test as it depends on having access to
a Kubeflow deployment to submit the TFJob to.

Python Path Requirements:
  kubeflow/tf-operator/py - https://github.com/kubeflow/tf-operator
     * Provides utilities for testing TFJobs
  kubeflow/testing/py - https://github.com/kubeflow/testing/tree/master/py
     * Provides utilities for testing

Manually running the test
 1. Configure your KUBECONFIG file to point to the desired cluster
 2. Set --params=name=${NAME},namespace=${NAMESPACE}
    * name should be the name for your job
    * namespace should be the namespace to use
 3. To test a new image set the parameter image e.g
     --params=name=${NAME},namespace=${NAMESPACE},image=${IMAGE}
 4. To control how long it trains set sample_size and num_epochs
     --params=num_epochs=1,sample_size=10,...
"""

# import json
import logging
import os
# import unittest

# from kubernetes import client as k8s_client
# from kubeflow.tf_operator import tf_job_client #pylint: disable=no-name-in-module
from kubeflow.tf_operator import test_runner #pylint: disable=no-name-in-module

from kubeflow.testing import ks_util
from kubeflow.testing import test_util
# from kubeflow.testing import util

class TFJobTest(test_util.TestCase):
  def __init__(self, args):
    namespace, name, env = test_runner.parse_runtime_params(args)
    self.app_dir = args.app_dir

    if not self.app_dir:
      self.app_dir = os.path.join(os.path.dirname(__file__), "..",
                                  "ks_app")
      self.app_dir = os.path.abspath(self.app_dir)
      logging.info("--app_dir not set defaulting to: %s", self.app_dir)

    self.env = env
    self.namespace = namespace
    self.params = args.params
    self.ks_cmd = ks_util.get_ksonnet_cmd(self.app_dir)
    super(TFJobTest, self).__init__(class_name="TFJobTest", name=name)

  # @unittest.expectedFailure
  # def test_train(self):
  #   # We repeat the test multiple times.
  #   # This ensures that if we delete the job we can create a new job with the
  #   # same name.
  #   api_client = k8s_client.ApiClient()

  #   component = "tfjob"
  #   # Setup the ksonnet app
  #   ks_util.setup_ks_app(self.app_dir, self.env, self.namespace, component,
  #                        self.params)


  #   # Create the TF job
  #   util.run([self.ks_cmd, "apply", self.env, "-c", component],
  #            cwd=self.app_dir)
  #   logging.info("Created job %s in namespaces %s", self.name, self.namespace)

  #   # Wait for the job to complete.
  #   logging.info("Waiting for job to finish.")
  #   results = tf_job_client.wait_for_job(
  #         api_client,
  #         self.namespace,
  #         self.name,
  #         status_callback=tf_job_client.log_status)
  #   logging.info("Final TFJob:\n %s", json.dumps(results, indent=2))

  #   # Check for errors creating pods and services. Can potentially
  #   # help debug failed test runs.
  #   creation_failures = tf_job_client.get_creation_failures_from_tfjob(
  #       api_client, self.namespace, results)
  #   if creation_failures:
  #     logging.warning(creation_failures)

  #   if not tf_job_client.job_succeeded(results):
  #     self.failure = "Job {0} in namespace {1} in status {2}".format(  # pylint: disable=attribute-defined-outside-init
  #         self.name, self.namespace, results.get("status", {}))
  #     logging.error(self.failure)
  #     return

  #   # We don't delete the jobs. We rely on TTLSecondsAfterFinished
  #   # to delete old jobs. Leaving jobs around should make it
  #   # easier to debug.

if __name__ == "__main__":
  test_runner.main(module=__name__)
