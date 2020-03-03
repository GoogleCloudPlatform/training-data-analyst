from setuptools import find_packages
from setuptools import setup

REQUIRED_PACKAGES = [
  'tensor2tensor'
]

setup(
    name='ghsumm',
    version='0.1',
    author='Google',
    author_email='training-feedback@cloud.google.com',
    install_requires=REQUIRED_PACKAGES,
    packages=find_packages(),
    include_package_data=True,
    description='Github Problem',
    requires=[]
)
