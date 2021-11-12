#!/bin/bash

python3 -m pip install tensorflow-model-analysis

jupyter nbextension enable --py widgetsnbextension
jupyter nbextension install --py --symlink tensorflow_model_analysis
jupyter nbextension enable --py tensorflow_model_analysis

service jupyter restart
