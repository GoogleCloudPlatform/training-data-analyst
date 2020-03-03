from setuptools import find_packages
from setuptools import setup

REQUIRED_PACKAGES = [
    'Keras==2.2.4'
]

setup(
  name="custom_prediction_routine",
  version="0.2",
  include_package_data=True,
  install_requires=REQUIRED_PACKAGES,
  packages=find_packages(),
  scripts=["model_prediction.py", "text_preprocessor.py"]
)
