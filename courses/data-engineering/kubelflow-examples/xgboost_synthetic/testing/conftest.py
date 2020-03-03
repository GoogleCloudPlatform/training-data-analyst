import pytest

def pytest_addoption(parser):
  parser.addoption(
    "--name", help="Name for the job. If not specified one was created "
    "automatically", type=str, default="")
  parser.addoption(
    "--namespace", help=("The namespace to run in. This should correspond to"
                         "a namespace associated with a Kubeflow namespace."),
                   type=str,
    default="kubeflow-kubeflow-testing")
  parser.addoption(
    "--image", help="Notebook image to use", type=str,
    default="gcr.io/kubeflow-images-public/tensorflow-1.14.0-notebook-gpu"
    ":v0.7.0")
  parser.addoption(
    "--repos", help="The repos to checkout; leave blank to use defaults",
    type=str, default="")

@pytest.fixture
def name(request):
  return request.config.getoption("--name")

@pytest.fixture
def namespace(request):
  return request.config.getoption("--namespace")

@pytest.fixture
def image(request):
  return request.config.getoption("--image")

@pytest.fixture
def repos(request):
  return request.config.getoption("--repos")
