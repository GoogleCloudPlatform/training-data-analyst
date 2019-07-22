"""setup.py required for training a model using ML Engine."""

from setuptools import find_packages
from setuptools import setup

REQUIRED_PACKAGES = ['docopt', 'moviepy', 'gym', 'gym[atari]']

setup(
    name='cartpole_pg',
    version='0.1',
    install_requires=REQUIRED_PACKAGES,
    packages=find_packages(),
    description=
    'Example for training RL agents using Cloud Hyperparameter tuning.')
