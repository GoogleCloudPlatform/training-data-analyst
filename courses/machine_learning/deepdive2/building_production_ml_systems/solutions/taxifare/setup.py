"""Setup."""
from os import path
from setuptools import find_packages
from setuptools import setup

setup(
    name='taxifare',
    version='0.1',
    packages=find_packages(exclude=['tests', 'notebooks'])
)
