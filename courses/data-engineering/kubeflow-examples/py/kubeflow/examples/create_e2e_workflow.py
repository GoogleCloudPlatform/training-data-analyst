""""Define the E2E workflow for kubeflow examples.

Rapid iteration.

Here are some pointers for rapidly iterating on the workflow during development.

1. You can use the e2e_tool.py to directly launch the workflow on a K8s cluster.
   If you don't have CLI access to the kubeflow-ci cluster (most folks) then
   you would need to setup your own test cluster.

2. Running with the E2E tool.

export PYTHONPATH=${PYTHONPATH}:${KUBEFLOW_EXAMPLES}/py:${KUBEFLOW_TESTING_REPO}/py

python -m kubeflow.testing.e2e_tool apply \
  kubeflow.examples.create_e2e_workflow.create_workflow
  --name=${USER}-kfctl-test-$(date +%Y%m%d-%H%M%S) \
  --namespace=kubeflow-test-infra \
  --open-in-chrome=true

To use code from a pull request set the prow envariables; e.g.

export JOB_NAME="jlewi-test"
export JOB_TYPE="presubmit"
export BUILD_ID=1234
export PROW_JOB_ID=1234
export REPO_OWNER=kubeflow
export REPO_NAME=kubeflow
export PULL_NUMBER=4148
"""

import logging
import os

from kubeflow.testing import argo_build_util

# The name of the NFS volume claim to use for test files.
NFS_VOLUME_CLAIM = "nfs-external"
# The name to use for the volume to use to contain test data
DATA_VOLUME = "kubeflow-test-volume"

# This is the main dag with the entrypoint
E2E_DAG_NAME = "e2e"
EXIT_DAG_NAME = "exit-handler"

# This is a sub dag containing the suite of tests to run against
# Kubeflow deployment
TESTS_DAG_NAME = "gke-tests"

TEMPLATE_LABEL = "examples_e2e"

MAIN_REPO = "kubeflow/examples"

EXTRA_REPOS = ["kubeflow/testing@HEAD", "kubeflow/tf-operator@HEAD"]

PROW_DICT = argo_build_util.get_prow_dict()

class Builder:
  def __init__(self, name=None, namespace=None, test_target_name=None,
               bucket=None,
               **kwargs): # pylint: disable=unused-argument
    """Initialize a builder.

    Args:
      name: Name for the workflow.
      namespace: Namespace for the workflow.
      test_target_name: (Optional) Name to use as the test target to group
        tests.
    """
    self.name = name
    self.namespace = namespace
    # ****************************************************************************
    # Define directory locations
    # ****************************************************************************
    # mount_path is the directory where the volume to store the test data
    # should be mounted.
    self.mount_path = "/mnt/" + "test-data-volume"
    # test_dir is the root directory for all data for a particular test run.
    self.test_dir = self.mount_path + "/" + self.name
    # output_dir is the directory to sync to GCS to contain the output for this
    # job.
    self.output_dir = self.test_dir + "/output"

    # We prefix the artifacts directory with junit because
    # that's what spyglass/prow requires. This ensures multiple
    # instances of a workflow triggered by the same prow job
    # don't end up clobbering each other
    self.artifacts_dir = self.output_dir + "/artifacts/junit_{0}".format(name)

    # source directory where all repos should be checked out
    self.src_root_dir = self.test_dir + "/src"
    # The directory containing the kubeflow/examples repo
    self.src_dir = self.src_root_dir + "/kubeflow/examples"

    # Top level directories for python code
    self.kubeflow_py = self.src_dir

    # The directory within the kubeflow_testing submodule containing
    # py scripts to use.
    self.kubeflow_testing_py = self.src_root_dir + "/kubeflow/testing/py"

    # The directory within the tf-operator submodule containing
    # py scripts to use.
    self.kubeflow_tfjob_py = self.src_root_dir + "/kubeflow/tf-operator/py"

    # The class name to label junit files.
    # We want to be able to group related tests in test grid.
    # Test grid allows grouping by target which corresponds to the classname
    # attribute in junit files.
    # So we set an environment variable to the desired class name.
    # The pytest modules can then look at this environment variable to
    # explicitly override the classname.
    # The classname should be unique for each run so it should take into
    # account the different parameters
    self.test_target_name = test_target_name

    self.bucket = bucket
    self.workflow = None

  def _build_workflow(self):
    """Create the scaffolding for the Argo workflow"""
    workflow = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Workflow",
        "metadata": {
            "name": self.name,
            "namespace": self.namespace,
            "labels": argo_build_util.add_dicts([{
              "workflow": self.name,
                "workflow_template": TEMPLATE_LABEL,
                }, argo_build_util.get_prow_labels()]),
        },
        "spec": {
            "entrypoint": E2E_DAG_NAME,
            # Have argo garbage collect old workflows otherwise we overload the API
            # server.
            "ttlSecondsAfterFinished": 7 * 24 * 60 * 60,
            "volumes": [
                {
                    "name": "gcp-credentials",
                    "secret": {
                        "secretName": "kubeflow-testing-credentials",
                      },
                  },
                {
                    "name": DATA_VOLUME,
                    "persistentVolumeClaim": {
                        "claimName": NFS_VOLUME_CLAIM,
                      },
                  },
              ],
            "onExit": EXIT_DAG_NAME,
            "templates": [
                {
                    "dag": {
                        "tasks": [],
                      },
                    "name": E2E_DAG_NAME,
                  },
                {
                    "dag": {
                        "tasks": [],
                      },
                    "name": TESTS_DAG_NAME,

                  },
                {
                    "dag": {
                        "tasks": [],
                      },
                    "name": EXIT_DAG_NAME,
                  }
              ],
          },  # spec
    }  # workflow

    return workflow

  def _build_task_template(self):
    """Return a template for all the tasks"""

    task_template = {'activeDeadlineSeconds': 3000,
                     'container': {'command': [],
                                   'env': [
                         {"name": "GOOGLE_APPLICATION_CREDENTIALS",
                          "value": "/secret/gcp-credentials/key.json"},
                         {"name": "TEST_TARGET_NAME",
                          "value": self.test_target_name},
                     ],
                         'image': 'gcr.io/kubeflow-ci/test-worker:latest',
                         'imagePullPolicy': 'Always',
                         'name': '',
                         'resources': {'limits': {'cpu': '4', 'memory': '4Gi'},
                                       'requests': {'cpu': '1', 'memory': '1536Mi'}},
                         'volumeMounts': [{'mountPath': '/mnt/test-data-volume',
                                           'name': 'kubeflow-test-volume'},
                                          {'mountPath':
                                           '/secret/gcp-credentials',
                                           'name': 'gcp-credentials'}]},
                     'metadata': {'labels': {
                         'workflow_template': TEMPLATE_LABEL}},
                     'outputs': {}}

    # Define common environment variables to be added to all steps
    common_env = [
        {'name': 'PYTHONPATH',
         'value': ":".join([self.kubeflow_py, self.kubeflow_py + "/py",
                            self.kubeflow_testing_py, self.kubeflow_tfjob_py])},
        {'name': 'KUBECONFIG',
         'value': os.path.join(self.test_dir, 'kfctl_test/.kube/kubeconfig')},
    ]

    task_template["container"]["env"].extend(common_env)

    task_template = argo_build_util.add_prow_env(task_template)

    return task_template

  def _build_step(self, name, workflow, dag_name, task_template,
                  command, dependencies):
    """Syntactic sugar to add a step to the workflow"""

    step = argo_build_util.deep_copy(task_template)

    step["name"] = name
    step["container"]["command"] = command

    argo_build_util.add_task_to_dag(workflow, dag_name, step, dependencies)

    # Return the newly created template; add_task_to_dag makes a copy of the template
    # So we need to fetch it from the workflow spec.
    for t in workflow["spec"]["templates"]:
      if t["name"] == name:
        return t

    return None

  def _build_tests_dag_notebooks(self):
    """Build the dag for the set of tests to run against a KF deployment."""

    task_template = self._build_task_template()

    # ***************************************************************************
    # Test xgboost
    step_name = "xgboost-synthetic"
    command = ["pytest", "xgboost_test.py",
               # Increase the log level so that info level log statements show up.
               "--log-cli-level=info",
               "--log-cli-format='%(levelname)s|%(asctime)s|%(pathname)s|%(lineno)d| %(message)s'",
               # Test timeout in seconds.
               "--timeout=1800",
               "--junitxml=" + self.artifacts_dir + "/junit_xgboost-synthetic-test.xml",
               ]

    dependencies = []
    xgboost_step = self._build_step(step_name, self.workflow, TESTS_DAG_NAME, task_template,
                                    command, dependencies)
    xgboost_step["container"]["workingDir"] = os.path.join(self.src_dir,
                                                           "xgboost_synthetic",
                                                           "testing")

  def _build_tests_dag_mnist(self):
    """Build the dag for the set of tests to run mnist TFJob tests."""

    task_template = self._build_task_template()

    # ***************************************************************************
    # Build mnist image
    step_name = "build-image"
    train_image_base = "gcr.io/kubeflow-examples/mnist"
    train_image_tag = "build-" + PROW_DICT['BUILD_ID']
    command = ["/bin/bash",
               "-c",
               "gcloud auth activate-service-account --key-file=$(GOOGLE_APPLICATION_CREDENTIALS) \
                && make build-gcb IMG=" + train_image_base + " TAG=" + train_image_tag,
              ]
    dependencies = []
    build_step = self._build_step(step_name, self.workflow, TESTS_DAG_NAME, task_template,
                                   command, dependencies)
    build_step["container"]["workingDir"] = os.path.join(self.src_dir, "mnist")

    # ***************************************************************************
    # Test mnist TFJob
    step_name = "tfjob-test"
    # Using python2 to run the test to avoid dependency error.
    command = ["python2", "-m", "pytest", "tfjob_test.py",
               # Increase the log level so that info level log statements show up.
               "--log-cli-level=info",
               "--log-cli-format='%(levelname)s|%(asctime)s|%(pathname)s|%(lineno)d| %(message)s'",
               # Test timeout in seconds.
               "--timeout=1800",
               "--junitxml=" + self.artifacts_dir + "/junit_tfjob-test.xml",
               ]

    dependencies = [build_step['name']]
    tfjob_step = self._build_step(step_name, self.workflow, TESTS_DAG_NAME, task_template,
                                   command, dependencies)
    tfjob_step["container"]["workingDir"] = os.path.join(self.src_dir,
                                                           "mnist",
                                                           "testing")

    # ***************************************************************************
    # Test mnist deploy
    step_name = "deploy-test"
    command = ["python2", "-m", "pytest", "deploy_test.py",
               # Increase the log level so that info level log statements show up.
               "--log-cli-level=info",
               "--log-cli-format='%(levelname)s|%(asctime)s|%(pathname)s|%(lineno)d| %(message)s'",
               # Test timeout in seconds.
               "--timeout=1800",
               "--junitxml=" + self.artifacts_dir + "/junit_deploy-test.xml",
               ]

    dependencies = [tfjob_step["name"]]
    deploy_step = self._build_step(step_name, self.workflow, TESTS_DAG_NAME, task_template,
                                   command, dependencies)
    deploy_step["container"]["workingDir"] = os.path.join(self.src_dir,
                                                           "mnist",
                                                           "testing")
    # ***************************************************************************
    # Test mnist predict
    step_name = "predict-test"
    command = ["pytest", "predict_test.py",
               # Increase the log level so that info level log statements show up.
               "--log-cli-level=info",
               "--log-cli-format='%(levelname)s|%(asctime)s|%(pathname)s|%(lineno)d| %(message)s'",
               # Test timeout in seconds.
               "--timeout=1800",
               "--junitxml=" + self.artifacts_dir + "/junit_predict-test.xml",
               ]

    dependencies = [deploy_step["name"]]
    predict_step = self._build_step(step_name, self.workflow, TESTS_DAG_NAME, task_template,
                                   command, dependencies)
    predict_step["container"]["workingDir"] = os.path.join(self.src_dir,
                                                           "mnist",
                                                           "testing")

  def _build_exit_dag(self):
    """Build the exit handler dag"""
    task_template = self._build_task_template()

    # ***********************************************************************
    # Copy artifacts
    step_name = "copy-artifacts"
    command = ["python",
               "-m",
               "kubeflow.testing.prow_artifacts",
               "--artifacts_dir=" +
               self.output_dir,
               "copy_artifacts"]

    if self.bucket:
      command.append("--bucket=" + self.bucket)

    dependencies = []

    copy_artifacts = self._build_step(step_name, self.workflow, EXIT_DAG_NAME, task_template,
                                      command, dependencies)

    # TODO(jlewi): We may need to run this with retries kubeflow/kubeflow
    # has a python script run with retries; we might want to move that
    # over to kubeflow.testing and use it.
    step_name = "test-dir-delete"
    command = ["rm",
               "-rf",
               self.test_dir, ]
    dependencies = [copy_artifacts["name"]]
    copy_artifacts = self._build_step(step_name, self.workflow, EXIT_DAG_NAME, task_template,
                                      command, dependencies)

    # We don't want to run from the directory we are trying to delete.
    copy_artifacts["container"]["workingDir"] = "/"

  def build(self):
    self.workflow = self._build_workflow()
    task_template = self._build_task_template()

    # **************************************************************************
    # Checkout

    # create the checkout step
    main_repo = argo_build_util.get_repo_from_prow_env()
    if not main_repo:
      logging.info("Prow environment variables for repo not set")
      main_repo = MAIN_REPO + "@HEAD"
    logging.info("Main repository: %s", main_repo)
    repos = [main_repo]

    repos.extend(EXTRA_REPOS)

    #***************************************************************************
    # Checkout the code
    checkout = argo_build_util.deep_copy(task_template)

    checkout["name"] = "checkout"
    checkout["container"]["command"] = ["/usr/local/bin/checkout_repos.sh",
                                        "--repos=" + ",".join(repos),
                                        "--src_dir=" + self.src_root_dir]

    argo_build_util.add_task_to_dag(self.workflow, E2E_DAG_NAME, checkout, [])

    #***************************************************************************
    # Get credentials for the latest auto-deployed cluster

    credentials = argo_build_util.deep_copy(task_template)

    credentials["name"] = "get-credentials"
    credentials["container"]["command"] = ["python3",
                                           "-m",
                                           "kubeflow.testing."
                                           "get_kf_testing_cluster",
                                           "get-credentials",
                                           ]

    dependencies = [checkout["name"]]
    argo_build_util.add_task_to_dag(self.workflow, E2E_DAG_NAME, credentials,
                                    dependencies)

    #**************************************************************************
    # Run a dag of tests
    if self.test_target_name == "notebooks":
      self._build_tests_dag_notebooks()
    elif self.test_target_name == "mnist":
      self._build_tests_dag_mnist()
    else:
      raise RuntimeError('Invalid test_target_name')

    # Add a task to run the dag
    dependencies = [credentials["name"]]
    argo_build_util.add_task_only_to_dag(self.workflow, E2E_DAG_NAME,
                                         TESTS_DAG_NAME,
                                         TESTS_DAG_NAME,
                                         dependencies)

    # **************************************************************************
    # create_pr_symlink
    # ***************************************************************************
    # TODO(jlewi): run_e2e_workflow.py should probably create the PR symlink
    step_name = "create-pr-symlink"
    command = ["python",
               "-m",
               "kubeflow.testing.prow_artifacts",
               "--artifacts_dir=" + self.output_dir,
               "create_pr_symlink"]

    if self.bucket:
      command.append(self.bucket)

    dependencies = [checkout["name"]]
    self._build_step(step_name, self.workflow, E2E_DAG_NAME, task_template,
                     command, dependencies)

    self._build_exit_dag()

    # Set the labels on all templates
    self.workflow = argo_build_util.set_task_template_labels(self.workflow)

    return self.workflow

# TODO(jlewi): This is an unnecessary layer of indirection around the builder
# We should allow py_func in prow_config to point to the builder and
# let e2e_tool take care of this.
def create_workflow(**kwargs):  # pylint: disable=too-many-statements
  """Create workflow returns an Argo workflow to test kfctl upgrades.

  Args:
    name: Name to give to the workflow. This can also be used to name things
     associated with the workflow.
  """

  builder = Builder(**kwargs)

  return builder.build()
