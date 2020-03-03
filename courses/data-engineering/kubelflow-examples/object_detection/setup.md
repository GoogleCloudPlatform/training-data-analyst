## Setup Kubeflow
### Requirements

 - Kubernetes cluster
 - Access to a working `kubectl` (Kubernetes CLI)
 - Ksonnet CLI: [ks](https://ksonnet.io/)

### Setup
Refer to the [getting started guide](https://www.kubeflow.org/docs/started/getting-started) for instructions on how to setup kubeflow on your kubernetes cluster. Specifically, look at the [quick start](https://www.kubeflow.org/docs/started/getting-started/#quick-start) section.
For this example, we will be using ks `nocloud` environment (on premise K8s). If you plan to use `cloud` ks environment, please make sure you follow the proper instructions in the kubeflow getting started guide.

After completing the steps in the kubeflow getting started guide you will have the following:
- A ksonnet app directory called `my-kubeflow` 
- A new namespace in you K8s cluster called `kubeflow`
- The following pods in your kubernetes cluster in the `kubeflow` namespace:
```
$ kubectl -n kubeflow get pods
NAME                                      READY     STATUS    RESTARTS   AGE
ambassador-7987df44b9-4pht8               2/2       Running   0          1m
ambassador-7987df44b9-dh5h6               2/2       Running   0          1m
ambassador-7987df44b9-qrgsm               2/2       Running   0          1m
tf-hub-0                                  1/1       Running   0          1m
tf-job-operator-v1alpha2-b76bfbdb-lgbjw   1/1       Running   0          1m
```

## Overview

During the course of this tutorial you will apply a set of ksonnet components that will:

1. Create a PersistentVolume to store our data and training results.
2. Download the dataset, dataset annotations, a pre-trained model checkpoint, and the training pipeline configuration file.
3. Decompress the downloaded dataset, pre-trained model, and dataset annotations.
4. Create a TensorFlow pet record since we will be training a pet detector model.
5. Execute a distributed TensorFlow object detection training job using the previous configurations.
6. Export the trained pet detector model and serve it using TF-Serving

We have prepared a ksonnet app `ks-app` with a set of components that will be used in this example.
The components can be found at the [ks-app/components](./ks-app/components) directory in case you want to perform some
customizations.

Let's make use of the app to continue with the tutorial.

```
cd ks-app
ENV=default
ks env add ${ENV} --context=`kubectl config current-context`
ks env set ${ENV} --namespace kubeflow
```

## Preparing the training data

**Note:** TensorFlow works with many file systems like HDFS and S3, you can use
them to push the dataset and other configurations there and skip the Download and Decompress steps in this tutorial.

First let's create a PVC to store the data.

```
# First, lets configure and apply the pets-pvc to create a PVC where the training data will be stored
ks param set pets-pvc accessMode "ReadWriteMany"
ks param set pets-pvc storage "20Gi"
ks apply ${ENV} -c pets-pvc
```

The command above will create a PVC with `ReadWriteMany` access mode if your Kubernetes cluster
does not support this feature you can modify the `accessMode` value to create the PVC in `ReadWriteOnce`
and before you execute the tf-job to train the model add a `nodeSelector:` configuration to execute the pods
in the same node. You can find more about assigning pods to specific nodes [here](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/)

This step assumes that your K8s cluster has [Dynamic Volume Provisioning](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning/) enabled and
the default Storage Class is created. You can check if the assumption is ready like below (a storageclass with `(default)` notation need exist):

```
$ kubectl get storageclass
NAME                 PROVISIONER               AGE
standard (default)   kubernetes.io/gce-pd      1d
gold                 kubernetes.io/gce-pd      1d
```

Otherwise you can find that the PVC remains `Pending` status.

```
$ kubectl get pvc pets-pvc -n kubeflow
NAME        STATUS    VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
pets-pvc    Pending                                                      28s
```

If your cluster doesn't have defined default storageclass, you can create a [PersistentVolume](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) manually to make the PVC work.

Now we will get the data we need to prepare our training pipeline:

```
# Configure and apply the get-data-job component this component will download the dataset,
# annotations, the model we will use for the fine tune checkpoint, and
# the pipeline configuration file

PVC="pets-pvc"
MOUNT_PATH="/pets_data"
DATASET_URL="http://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz"
ANNOTATIONS_URL="http://www.robots.ox.ac.uk/~vgg/data/pets/data/annotations.tar.gz"
MODEL_URL="http://download.tensorflow.org/models/object_detection/faster_rcnn_resnet101_coco_2018_01_28.tar.gz"
PIPELINE_CONFIG_URL="https://raw.githubusercontent.com/kubeflow/examples/master/object_detection/conf/faster_rcnn_resnet101_pets.config"

ks param set get-data-job mounthPath ${MOUNT_PATH}
ks param set get-data-job pvc ${PVC}
ks param set get-data-job urlData ${DATASET_URL}
ks param set get-data-job urlAnnotations ${ANNOTATIONS_URL}
ks param set get-data-job urlModel ${MODEL_URL}
ks param set get-data-job urlPipelineConfig ${PIPELINE_CONFIG_URL}

ks apply ${ENV} -c get-data-job
```
The downloaded files will be dumped into the `MOUNT_PATH`

Here is a quick description for the `get-data-job` component parameters:

- `mountPath` string, volume mount path.
- `pvc` string, name of the PVC where the data will be stored.
- `urlData` string, remote URL of the dataset that will be used for training.
- `urlAnnotations` string, remote URL of the annotations that will be used for training.
- `urlModel` string, remote URL of the model that will be used for fine tuning.
- `urlPipelineConfig` string, remote URL of the pipeline configuration file to use.

**NOTE:** The annotations are the result of labeling your dataset using some manual labeling tool. For this example we will use
a set of annotations generated specifically for the dataset we are using for training.

Before moving to the next set of commands make sure all of the jobs to get the data were completed.

Now we will configure and apply the `decompress-data-job` component:

```
ANNOTATIONS_PATH="${MOUNT_PATH}/annotations.tar.gz"
DATASET_PATH="${MOUNT_PATH}/images.tar.gz"
PRE_TRAINED_MODEL_PATH="${MOUNT_PATH}/faster_rcnn_resnet101_coco_2018_01_28.tar.gz"

ks param set decompress-data-job mountPath ${MOUNT_PATH}
ks param set decompress-data-job pvc ${PVC}
ks param set decompress-data-job pathToAnnotations ${ANNOTATIONS_PATH}
ks param set decompress-data-job pathToDataset ${DATASET_PATH}
ks param set decompress-data-job pathToModel ${PRE_TRAINED_MODEL_PATH}

ks apply ${ENV} -c decompress-data-job
```

Here is a quick description for the `decompress-data-job` component parameters:

- `mountPath` string, volume mount path.
- `pvc` string, name of the PVC where the data is located.
- `pathToAnnotations` string, File system path to the annotations .tar.gz file
- `pathToDataset` string, File system path to the dataset .tar.gz file
- `pathToModel` string, File system path to the pre-trained model .tar.gz file

Finally, and since TensorFlow Object Detection API uses the [TFRecord format](https://www.tensorflow.org/api_guides/python/python_io#tfrecords_format_details)
we need to create the TF pet records. For that, we wil configure and apply the `create-pet-record-job` component:

```
OBJ_DETECTION_IMAGE="lcastell/pets_object_detection"
DATA_DIR_PATH="${MOUNT_PATH}"
OUTPUT_DIR_PATH="${MOUNT_PATH}"

ks param set create-pet-record-job image ${OBJ_DETECTION_IMAGE}
ks param set create-pet-record-job dataDirPath ${DATA_DIR_PATH}
ks param set create-pet-record-job outputDirPath ${OUTPUT_DIR_PATH}
ks param set create-pet-record-job mountPath ${MOUNT_PATH}
ks param set create-pet-record-job pvc ${PVC}

ks apply ${ENV} -c create-pet-record-job
```

Here is a quick description for the `create-pet-record-job` component parameters:

- `mountPath` string, volume mount path.
- `pvc` string, name of the PVC where the data is located.
- `image` string, name of the docker image to use.
- `dataDirPath` string, the directory with the images
- `outputDirPath` string, the output directory for the pet records.

To see the default values of the components used in this set of steps look at: [params.libsonnet](./ks-app/components/params.libsonnet)

## Next
[Submit the TF Job](submit_job.md)
