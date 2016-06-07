#!/bin/bash
gsutil cp *.csv gs://cloud-training-demos/flights/
gsutil acl ch -R -g google.com:R gs://cloud-training-demos/flights/
