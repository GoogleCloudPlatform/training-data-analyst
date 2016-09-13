#!/bin/bash
PROJECT_ID=`gcloud config list project --format "value(core.project)"`
AUTH_TOKEN=`gcloud auth print-access-token`
SVC_ACCOUNT=`curl -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $AUTH_TOKEN" https://ml.googleapis.com/v1alpha3/projects/$PROJECT_ID:getConfig | python -c "import json; import sys; response = json.load(sys.stdin); print response['serviceAccount']"`
echo "$SVC_ACCOUNT"
