#!/bin/bash

# Continuous integration: recreate image anytime transform.py is commited into GitHub

# In order to try this out, fork this repo into your personal GitHub account
# Then, change the repo-owner to be your GitHub id
gcloud beta builds triggers create github --build-config=cloudbuild.yaml \
  --included-files="courses/machine_learning/deepdive/06_structured/pipelines/containers/bqtocsv/**" \
  --branch-pattern="^master$" \
  --repo-name="training-data-analyst" --repo-owner="GoogleCloudPlatform" 

