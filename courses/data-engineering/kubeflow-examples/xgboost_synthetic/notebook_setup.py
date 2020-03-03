"""Some routines to setup the notebook.

This is separated out from util.py because this module installs some of the pip packages
that util depends on.
"""
import sys
import logging
import os
import subprocess

from pathlib import Path

KFP_PACKAGE = 'https://storage.googleapis.com/ml-pipeline/release/0.1.32/kfp.tar.gz'
FAIRING_PACKAGE = 'git+git://github.com/kubeflow/fairing.git@9b0d4ed4796ba349ac6067bbd802ff1d6454d015' # pylint: disable=line-too-long

def notebook_setup():
  # Install the SDK
  logging.basicConfig(format='%(message)s')
  logging.getLogger().setLevel(logging.INFO)

  logging.info("pip installing requirements.txt")
  subprocess.check_call(["pip3", "install", "--user", "-r", "requirements.txt"])
  logging.info("pip installing KFP %s", KFP_PACKAGE)
  subprocess.check_call(["pip3", "install", "--user", KFP_PACKAGE, "--upgrade"])
  logging.info("pip installing fairing %s", FAIRING_PACKAGE)
  subprocess.check_call(["pip3", "install", "--user", FAIRING_PACKAGE])

  logging.info("Configure docker credentials")
  subprocess.check_call(["gcloud", "auth", "configure-docker", "--quiet"])
  if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    logging.info("Activating service account")
    subprocess.check_call(["gcloud", "auth", "activate-service-account",
                           "--key-file=" +
                           os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                           "--quiet"])

  home = str(Path.home())

  # Installing the python packages locally doesn't appear to have them automatically
  # added the path so we need to manually add the directory
  local_py_path = os.path.join(home, ".local/lib/python3.6/site-packages")
  if local_py_path not in sys.path:
    logging.info("Adding %s to python path", local_py_path)
    # Insert at front because we want to override any installed packages
    sys.path.insert(0, local_py_path)
