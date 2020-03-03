# Kubeflow MPI Horovod example

This example deploys MPI operator into kubeflow cluster and runs an distributed training example using GPU. 

## Steps


* Deploy [kubeflow cluster (version v0.7.0)](https://www.kubeflow.org/docs/gke/deploy/)
* Add GPU node pool to newly created kubeflow cluster (might need to increase quotas if needed):
```
export PROJECT=
export CLUSTER=
gcloud container node-pools create gpu-pool-mpi --accelerator=type=nvidia-tesla-k80,count=4 --cluster=$CLUSTER --project=$PROJECT --machine-type=n1-standard-8 --num-nodes=2
```
* Deploy MPI operator into kubeflow cluster: from [kubeflow manifests](https://github.com/kubeflow/manifests) repo, run 
```
kustomize build mpi-job/mpi-operator/base/ | kubectl apply -f -
```
* Deploy the MPI exmaple job:
```
kubectl apply -f mpi-job.yaml -n kubeflow
```
* Once launcher pod is up and running, log will be available from:
```
POD_NAME=$(kubectl -n kubeflow get pods -l mpi_job_name=tf-resnet50-horovod-job,mpi_role_type=launcher -o name)
kubectl -n kubeflow logs -f ${POD_NAME}
```