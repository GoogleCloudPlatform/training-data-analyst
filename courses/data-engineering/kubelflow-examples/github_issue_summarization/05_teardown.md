# Teardown

If you created a cluster with Click-to-Deploy or `kfctl`, delete the deployment
using the [GCP console](https://console.cloud.google.com/dm/deployments). The
default deployment name is `kubeflow`.

Delete the PD (persistent disk) backing the NFS mount.

```bash
gcloud --project=${PROJECT} compute disks delete  --zone=${ZONE} ${PD_DISK_NAME}
```

*Back*: [Querying the model](04_querying_the_model.md)
