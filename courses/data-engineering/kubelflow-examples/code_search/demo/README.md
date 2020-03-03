# Demo

This directory contains assets for setting up a demo of the code search example.
It is primarily intended for use by Kubeflow contributors working on the shared demo.

Users looking to run the example should follow the README.md in the parent directory.

# GCP Resources

We are using the following project

* **org**: kubeflow.org
* **project**: code-search-demo
* **[code-search-team@kubeflow.org](https://github.com/kubeflow/internal-acls/blob/master/code-search-team.members.txt)** Google group administering access

# Deploying the services

1. Deploy the TFServing server

   ```
   ks12 show  cs_demo -c t2t-code-search-serving
   ```

1. Deploy the UI and nmslib index server

   ```
   ks12 apply  cs_demo -c search-index-server
   ```

1. Copy the GCP service account to the namespace where the servers run

   * The serving piece runs in a different namespace from Kubeflow
   * We need to copy the GCP service account to that namespace because the pod will try to mount it.

   ```
   kubectl -n kubeflow get secret user-gcp-sa -o json | jq -r '.data["user-gcp-sa.json"]' | base64 -d > ${SECRET_FILE}
   kubectl -n cs-web-app create secret generic user-gcp-sa --from-file=user-gcp-sa.json=${SECRET_FILE}
   ```
# Install Argo CD

```
kubectl create namespace argocd
cd cs-demo-1103/k8s_specs
kubectl apply -f argocd.yaml
```

Create the app

```
SRC_URL=https://github.com/kubeflow/examples.git
KS_PATH=code_search/kubeflow
argocd app create code-search --name kubeflow --repo $SRC_URL --path ${KS_PATH} --env ${KS_ENV}
```
# Results

## 2018-11-05

jlewi@ ran experiments that produced the following results

| What | location | Description
|------|----------|-------------------------
| Preprocessed data|  gs://code-search-demo/20181104/data/func-doc-pairs-00???-of-00100.csv |  This is the output of the Dataflow preprocessing job
| Training data | gs://code-search-demo/20181104/data/kf_github_function_docstring-train-00???-of-00100 | TFRecord files produced by running T2T datagen


### Models

| hparams | Location 
|---------| -------- 
| transformer_tine | gs://code-search-demo/models/20181105-tinyparams/
| transformer_base_single_gpu | gs://code-search-demo/models/20181105-single-gpu
| transformer_base | gs://code-search-demo/models/20181107-dist-sync-gpu

## Performance

| hparams | Resources | Steps/sec
|----------|----------|---------------------
| transformer_tiny | 1 CPU worker|  ~1.8 global step /sec
| transformer_base_single_gpu | 1 GPU worker (K80) | ~3.22611 global step /sec
| transformer_base | 1 chief with K80, 8 workers with 1 K80, sync training| ~ 0.0588723 global step /sec
| transformer_base | 1 chief (no GPU), 8 workers (no GPU), sync training| ~ 0.707014 global step /sec
