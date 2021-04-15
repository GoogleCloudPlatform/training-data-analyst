# Build, Train and Deploy with Drift, Outlier Detectors and Explainers enabled on KFServing and Seldon

These examples show how to build a model and then deploy with [KFServing](https://github.com/kubeflow/kfserving) or [Seldon Core](https://github.com/SeldonIO/seldon-core) with model explainers, drift detectors and outlier detectors. The pipelines are built using [Kale](https://github.com/kubeflow-kale/kale).

## Examples

 * [Seldon](./seldon/README.md)
 * [KFServing](./kfserving/README.md) 


## GCP Setup

For a GCP cluster we need a RWX Persistent Volume for the shared data Kale needs. To set this up on GCP update and run the script `gcp-create-rwx-pv.sh` after setting the values for your project, Filestore name and Zone:

```
PROJECT=seldon-demos
FS=pipeline-data
ZONE=europe-west1-b    

gcloud beta filestore instances create ${FS}     --project=${PROJECT}     --zone=${ZONE}     --tier=STANDARD     --file-share=name="volumes",capacity=1TB     --network=name="default",reserved-ip-range="10.0.0.0/29"

FSADDR=$(gcloud beta filestore instances describe ${FS} --project=${PROJECT} --zone=${ZONE} --format="value(networks.ipAddresses[0])")

helm install nfs-cp stable/nfs-client-provisioner --set nfs.server=${FSADDR} --set nfs.path=/volumes --namespace=kubeflow 

kubectl rollout status  deploy/nfs-cp-nfs-client-provisioner -n kubeflow
```

If you build the pipeline Python DSL using Kale from the notebook you will at present need to modify the created pyhton and change the Kale `VolumeOp` by adding a `storage_class` for the NFS PV, for example:

```
marshal_vop = dsl.VolumeOp(
     name="kale-marshal-volume",
     resource_name="kale-marshal-pvc",
     storage_class="nfs-client",
     modes=dsl.VOLUME_MODE_RWM,
     size="1Gi")
```

## Tested on

If you have tested these pipelines successfully please add a PR to extend the table below.

| K8S | Kubeflow | Knative Eventing | Seldon | KFServing | Kale | Notes
| ----| -------  | ---------------- | ------ | --------- | ---- | ----- |
| GKE 1.14.10 | 1.0 | 0.11 | 1.2.1 | 0.3.0 | 0.5.0 | GCP Setup above, Kale storage_class fix |







   
