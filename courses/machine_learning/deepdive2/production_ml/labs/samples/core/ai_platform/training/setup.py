# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Dependencies for Dataflow workers.'''

from setuptools import setup, find_packages
import os

NAME = 'chicago_crime_trainer'
VERSION = '0.0'
REQUIRED_PACKAGES = ['numpy>=1.14','pandas>=0.22','scikit-learn>=0.20.2','tensorflow>=1.13,<2']


setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(),
    install_requires=REQUIRED_PACKAGES,    
    )
