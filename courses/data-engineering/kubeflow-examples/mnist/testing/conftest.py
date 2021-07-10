import os
import pytest

def pytest_addoption(parser):

  parser.addoption(
    "--tfjob_name", help="Name for the TFjob.",
    type=str, default="mnist-test-" + os.getenv('BUILD_ID'))

  parser.addoption(
    "--namespace", help=("The namespace to run in. This should correspond to"
                         "a namespace associated with a Kubeflow namespace."),
    type=str, default="kubeflow-kubeflow-testing")

  parser.addoption(
    "--repos", help="The repos to checkout; leave blank to use defaults",
    type=str, default="")

  parser.addoption(
    "--trainer_image", help="TFJob training image",
    type=str, default="gcr.io/kubeflow-examples/mnist/model:build-" + os.getenv('BUILD_ID'))

  parser.addoption(
    "--train_steps", help="train steps for mnist testing",
    type=str, default="200")

  parser.addoption(
    "--batch_size", help="batch size for mnist trainning",
    type=str, default="100")

  parser.addoption(
    "--learning_rate", help="mnist learnning rate",
    type=str, default="0.01")

  parser.addoption(
    "--num_ps", help="The number of PS",
    type=str, default="1")

  parser.addoption(
    "--num_workers", help="The number of Worker",
    type=str, default="2")

  parser.addoption(
    "--model_dir", help="Path for model saving",
    type=str, default="gs://kubeflow-ci-deployment_ci-temp/mnist/models/" + os.getenv('BUILD_ID'))

  parser.addoption(
    "--export_dir", help="Path for model exporting",
    type=str, default="gs://kubeflow-ci-deployment_ci-temp/mnist/models/" + os.getenv('BUILD_ID'))

  parser.addoption(
    "--deploy_name", help="Name for the service deployment",
    type=str, default="mnist-test-" + os.getenv('BUILD_ID'))

  parser.addoption(
      "--master", action="store", default="", help="IP address of GKE master")

  parser.addoption(
      "--service", action="store", default="mnist-test-" + os.getenv('BUILD_ID'),
      help="The name of the mnist K8s service")

@pytest.fixture
def master(request):
  return request.config.getoption("--master")

@pytest.fixture
def namespace(request):
  return request.config.getoption("--namespace")

@pytest.fixture
def service(request):
  return request.config.getoption("--service")

@pytest.fixture
def tfjob_name(request):
  return request.config.getoption("--tfjob_name")

@pytest.fixture
def repos(request):
  return request.config.getoption("--repos")

@pytest.fixture
def trainer_image(request):
  return request.config.getoption("--trainer_image")

@pytest.fixture
def train_steps(request):
  return request.config.getoption("--train_steps")

@pytest.fixture
def batch_size(request):
  return request.config.getoption("--batch_size")

@pytest.fixture
def learning_rate(request):
  return request.config.getoption("--learning_rate")

@pytest.fixture
def num_ps(request):
  return request.config.getoption("--num_ps")

@pytest.fixture
def num_workers(request):
  return request.config.getoption("--num_workers")

@pytest.fixture
def model_dir(request):
  return request.config.getoption("--model_dir")

@pytest.fixture
def export_dir(request):
  return request.config.getoption("--export_dir")

@pytest.fixture
def deploy_name(request):
  return request.config.getoption("--deploy_name")
