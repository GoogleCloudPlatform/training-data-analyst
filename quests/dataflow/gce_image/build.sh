#!/bin/bash

IMAGE_NAME=theia-ide-training-data-analyst-v$(date +%Y%m%d)

gcloud builds submit . --config cloudbuild.yaml --project qwiklabs-resources \
  --timeout=15m \
  --substitutions=_IMAGE_NAME=$IMAGE_NAME