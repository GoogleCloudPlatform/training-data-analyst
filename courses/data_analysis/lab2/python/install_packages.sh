#!/bin/bash

apt-get install python-pip
pip install google-cloud-dataflow oauth2client==3.0.0 
pip install --force six==1.10  # downgrade as 1.11 breaks apitools
pip install -U pip
