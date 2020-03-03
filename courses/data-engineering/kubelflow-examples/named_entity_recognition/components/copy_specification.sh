#!/bin/sh

BUCKET="your-bucket-name"

echo "\nCopy component specifications to Google Cloud Storage"
gsutil cp preprocess/component.yaml gs://${BUCKET}/components/preprocess/component.yaml
gsutil acl ch -u AllUsers:R gs://${BUCKET}/components/preprocess/component.yaml

gsutil cp train/component.yaml gs://${BUCKET}/components/train/component.yaml
gsutil acl ch -u AllUsers:R gs://${BUCKET}/components/train/component.yaml

gsutil cp deploy/component.yaml gs://${BUCKET}/components/deploy/component.yaml
gsutil acl ch -u AllUsers:R gs://${BUCKET}/components/deploy/component.yaml