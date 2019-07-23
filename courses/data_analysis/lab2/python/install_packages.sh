#!/bin/bash

apt-get install python-pip
pip install -U pip
pip install apache-beam[gcp] oauth2client==3.0.0
