#!/bin/sh
docker run gcr.io/cloud-training-demos/babyweight-pipeline-deploycmle:latest gs://cloud-training-demos-ml/babyweight/hyperparam/15 babyweight local
