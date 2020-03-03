## Overview
This directory shows how to build a scheduled pipeline to periodically update the search index and update the search UI
using the new index. It also uses github to store the search UI's Kubernetes spec and hooks up Argo CD to automatically
update the search UI.

At a high level, the pipeline automate the process to 
1. Compute the function embeddings
2. Create new search index file
3. Update the github manifest pointing to the new search index file

ArgoCD then triggers a new service deployment with the new manifest.

## Perquisite
- A cluster with kubeflow deployed, including [kubeflow pipeline](https://github.com/kubeflow/pipelines)
- A pre trained code search model.


## Instruction
1. Upload the ks-web-app/ dir to a github repository, and set up Argo CD following the 
[instruction](https://github.com/argoproj/argo-cd/blob/master/docs/getting_started.md#6-create-an-application-from-a-git-repository-location)
Set up [Automated sync](https://github.com/argoproj/argo-cd/blob/master/docs/auto_sync.md) if you want the search UI to
be updated at real time. Otherwise Argo CD will pull latest config every 3 minutes as default.  
2. Create a github token following [instruction](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/#creating-a-token)
and store it in the cluster as secret. This allows pipeline to update github. The secret is stored in the kubeflow namespace, assuming it's the same namespace
as which the kubeflow is stored
 ```bash
kubectl create secret generic github-access-token --from-literal=token=[your_github_token] -n kubeflow
```
3. To run the pipeline, follow the kubeflow pipeline instruction and compile index_update_pipeline.py and upload to pipeline
page.

Provide the parameter, e.g. 
```
PROJECT='code-search-demo'
CLUSTER_NAME='cs-demo-1103'
WORKING_DIR='gs://code-search-demo/pipeline'
SAVED_MODEL_DIR='gs://code-search-demo/models/20181107-dist-sync-gpu/export/1541712907/'
DATA_DIR='gs://code-search-demo/20181104/data'
```

TODO(IronPan): more details on how to run pipeline
 