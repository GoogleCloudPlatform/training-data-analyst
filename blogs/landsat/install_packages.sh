#!/bin/bash

apt-get install libgdal-dev
pip install gdal==1.10.0 --global-option=build_ext --global-option="-I/usr/include/gdal/"


pip install google-cloud-dataflow
