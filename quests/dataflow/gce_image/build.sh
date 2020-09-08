#!/bin/bash

gcloud builds submit . --config cloudbuild.yaml --project qwiklabs-resources \
  --timeout=15m \
  --substitutions=_TIMESTAMP=$(date +%Y%m%d)