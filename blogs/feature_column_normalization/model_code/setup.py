"""setup.py required for training a model using ML Engine.
"""

from setuptools import find_packages
from setuptools import setup

REQUIRED_PACKAGES = ['docopt']

setup(
  name='normalized_housing_model',
  version='0.1',
  author = 'Chris Rawles',
  author_email = 'crawles@google.com',
  install_requires=REQUIRED_PACKAGES,
  packages=find_packages(),
  description='Example for training a model with input normalization.')
