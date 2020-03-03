import pytest

def pytest_addoption(parser):
  parser.addoption(
      "--master", action="store", default="", help="IP address of GKE master")

  parser.addoption(
      "--namespace", action="store", default="", help="namespace of server")

  parser.addoption(
      "--service", action="store", default="",
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
