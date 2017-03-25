#!/bin/bash

apt-get install python-pip
pip install google-cloud-dataflow oauth2client==3.0.0 
pip install -U pip

echo "Please type:"
echo "               pip -V "
echo "If you get a pip version that is less than 8.0, please log out and log back in"
