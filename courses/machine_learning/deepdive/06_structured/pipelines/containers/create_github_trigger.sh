#!/bin/bash -e

# Continuous integration: recreate image anytime any file
# in the directory that this script is run from is commited into GitHub
# Run this only once per directory
# In order to try this out, fork this repo into your personal GitHub account
# Then, change the repo-owner to be your GitHub id

DIR_IN_REPO=$(pwd | sed 's%training-data-analyst/% %g' | awk '{print $2}')
echo $DIR_IN_REPO

gcloud beta builds triggers create github \
  --build-config="${DIR_IN_REPO}/cloudbuild.yaml" \
  --included-files="${DIR_IN_REPO}/**" \
  --branch-pattern="^master$" \
  --repo-name="training-data-analyst" --repo-owner="GoogleCloudPlatform" 

