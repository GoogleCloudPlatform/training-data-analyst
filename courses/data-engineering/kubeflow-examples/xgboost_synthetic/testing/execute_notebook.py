import tempfile
import logging
import os
import subprocess


logger = logging.getLogger(__name__)

def prepare_env():
  subprocess.check_call(["pip3", "install", "-U", "papermill"])
  subprocess.check_call(["pip3", "install", "-r", "../requirements.txt"])


def execute_notebook(notebook_path, parameters=None):
  temp_dir = tempfile.mkdtemp()
  notebook_output_path = os.path.join(temp_dir, "out.ipynb")
  papermill.execute_notebook(notebook_path, notebook_output_path,
                             cwd=os.path.dirname(notebook_path),
                             parameters=parameters,
                             log_output=True)
  return notebook_output_path

def run_notebook_test(notebook_path, expected_messages, parameters=None):
  output_path = execute_notebook(notebook_path, parameters=parameters)
  actual_output = open(output_path, 'r').read()
  for expected_message in expected_messages:
    if not expected_message in actual_output:
      logger.error(actual_output)
      assert False, "Unable to find from output: " + expected_message

if __name__ == "__main__":
  prepare_env()
  import papermill #pylint: disable=import-error
  FILE_DIR = os.path.dirname(__file__)
  NOTEBOOK_REL_PATH = "../build-train-deploy.ipynb"
  NOTEBOOK_ABS_PATH = os.path.normpath(os.path.join(FILE_DIR, NOTEBOOK_REL_PATH))
  EXPECTED_MGS = [
      "Finished upload of",
      "Model export success: mockup-model.dat",
      "Pod started running True",
      "Cluster endpoint: http:",
  ]
  run_notebook_test(NOTEBOOK_ABS_PATH, EXPECTED_MGS)
