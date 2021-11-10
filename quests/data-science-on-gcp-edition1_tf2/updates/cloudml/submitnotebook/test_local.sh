#!/bin/sh
docker run gcr.io/cloud-training-demos/submitnotebook:latest gs://cloud-training-demos-ml/flights/notebook/flights_small.ipynb gs://cloud-training-demos-ml/flights/notebook/flights_small_kfp.ipynb gs://cloud-training-demos-ml/flights/notebook/params.yaml
