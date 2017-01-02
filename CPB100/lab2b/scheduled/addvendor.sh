#!/bin/bash

cp ../transform.py .
mkdir lib
pip install --target=lib \
    https://downloads.sourceforge.net/project/matplotlib/matplotlib-toolkits/basemap-1.0.7/basemap-1.0.7.tar.gz
