"""Setup."""
from os import path
from setuptools import find_packages
from setuptools import setup

HERE = path.abspath(path.dirname(__file__))

with open(path.join(HERE, 'requirements.txt')) as f:
  requirements = []
  for line in f:
    requirements.append(line.strip())

setup(
    name='taxifare',
    version='0.1',
    packages=find_packages(exclude=['tests', 'notebooks']),
    install_requires=requirements,
)
