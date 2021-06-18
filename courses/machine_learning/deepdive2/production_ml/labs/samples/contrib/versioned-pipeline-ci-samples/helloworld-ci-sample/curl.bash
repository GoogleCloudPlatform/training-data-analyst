#!/bin/bash

# strip gs:// prefix
bucket_name=$(echo $3 | sed 's/gs:\/\///')
data='{"name":'\""ci-$1"\"', "code_source_url": "https://github.com/kubeflow/pipelines/tree/'"$1"'", "package_url": {"pipeline_url": "https://storage.googleapis.com/'"$bucket_name"'/'"$1"'/pipeline.zip"}, 
"resource_references": [{"key": {"id": '\""$2"\"', "type":3}, "relationship":1}]}'

version=$(curl -H "Content-Type: application/json" -X POST -d "$data" "$4"/apis/v1beta1/pipeline_versions | jq -r ".id")

# create run
rundata='{"name":'\""$1-run"\"', 
"resource_references": [{"key": {"id": '\""$version"\"', "type":4}, "relationship":2}]}'
echo "$rundata"
curl -H "Content-Type: application/json" -X POST -d "$rundata" "$4"/apis/v1beta1/runs