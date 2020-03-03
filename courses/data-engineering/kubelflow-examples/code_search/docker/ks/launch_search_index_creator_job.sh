#!/bin/bash
# This script is a wrapper script for calling search index creator ksonnet component
# and creates a kubernetes job to compute search index.
# For more details about search index ksonnet component, check
# https://github.com/kubeflow/examples/blob/master/code_search/kubeflow/components/search-index-creator.jsonnet

set -ex

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null && pwd)"

# Providing negative value to kubeflow wait would wait for a week
timeout="-1s"
# Ksonnet Environment name. Always use pipeline
ksEnvName="pipeline"
# Search index creator ksonnet component name
component="search-index-creator"

usage() {
	echo "Usage: launch_search_index_creator_job.sh
	--cluster=<cluster to deploy job to>
	--functionEmbeddingsDir=<input function embedding dir>
	--indexFile=<index file>
	--lookupFile=<lookup file>
	--namespace=<kubernetes namespace>
	--timeout=<timeout>
	--workflowId=<workflow id invoking the container>"
}

# List of required parameters
names=(cluster functionEmbeddingsDir indexFile lookupFile namespace workflowId)

source "${DIR}/parse_arguments.sh"
source "${DIR}/initialize_kubectl.sh"

# Apply parameters
ks param set ${component} functionEmbeddingsDir ${functionEmbeddingsDir} --env ${ksEnvName}
ks param set ${component} indexFile ${indexFile} --env ${ksEnvName}
ks param set ${component} jobNameSuffix ${workflowId} --env ${ksEnvName}
ks param set ${component} lookupFile ${lookupFile} --env ${ksEnvName}

ks show ${ksEnvName} -c "${component}"
ks apply ${ksEnvName} -c "${component}"

JOB_NAME="pipeline-create-search-index-${workflowId}"
echo "wait for ${JOB_NAME} to finish"

kubectl wait --timeout="${timeout}" --for=condition=complete job/${JOB_NAME} -n "${namespace}"
# If the wait above failed, then the script will fail fast and following command won't run.
# TODO complete doesn't mean it's successful. Check the job succeeded.
echo "${JOB_NAME} is succeeded"
