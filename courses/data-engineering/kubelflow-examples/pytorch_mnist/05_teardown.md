# Teardown

Delete the Kubeflow deployment `namespace` using kfctl.sh tool as shown in step 6 [from the Kubeflow GKE documentation](https://www.kubeflow.org/docs/started/getting-started-gke/#deploy-kubeflow-on-kubernetes-engine).

```commandline
cd ${KFAPP}
${KUBEFLOW_REPO}/scripts/kfctl.sh delete all
```

[Delete the Cloud Filestore](https://cloud.google.com/filestore/docs/deleting-instances) shared persistent disk backing the NFS mount.

*Back*: [Querying the model](04_querying_the_model.md)
