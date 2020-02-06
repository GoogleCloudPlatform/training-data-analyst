#!/bin/bash

# Continuous integration: recreate image anytime transform.py is commited into GitHub
# In order to try this out, fork this repo into your personal GitHub account
# Then, change the repo-owner to be your GitHub id

DIR=$(pwd | sed 's/training-data-analyst/ /g' | awk '{print $2}')
echo $DIR

gcloud beta builds triggers create github \
  --build-config="${DIR}/cloudbuild.yaml" \
  --included-files="${DIR}/**" \
  --branch-pattern="^master$" \
  --repo-name="training-data-analyst" --repo-owner="GoogleCloudPlatform" 

