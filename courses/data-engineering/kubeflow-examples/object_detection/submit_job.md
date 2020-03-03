# Launch a distributed object detection training job
## Requirements

 - Docker
 - Docker Registry
 - Object Detection Training Docker Image

Build the TensorFlow object detection training image, or use the pre-built image `lcastell/pets_object_detection` in Docker hub.

## To build the image:
First copy the Dockerfile file from `./docker` directory into your $HOME path
```
# from your $HOME directory
docker build --pull -t $USER/pets_object_detection -f ./Dockerfile.training .
```

### Push the image to your docker registry
```
# from your $HOME directory
docker tag  $USER/pets_object_detection  <your_server:your_port>/pets_object_detection
docker push <your_server:your_port>/pets_object_detection
```

## Create  training TF-Job deployment and launching it

```
# from the ks-app directory

PIPELINE_CONFIG_PATH="${MOUNT_PATH}/faster_rcnn_resnet101_pets.config"
TRAINING_DIR="${MOUNT_PATH}/train"

ks param set tf-training-job image ${OBJ_DETECTION_IMAGE}
ks param set tf-training-job mountPath ${MOUNT_PATH}
ks param set tf-training-job pvc ${PVC}
ks param set tf-training-job numPs 1
ks param set tf-training-job numWorkers 1
ks param set tf-training-job pipelineConfigPath ${PIPELINE_CONFIG_PATH}
ks param set tf-training-job trainDir ${TRAINING_DIR}

ks apply ${ENV} -c tf-training-job
```
**NOTE**: The default `TFJob` api verison in the component is `kubeflow.org/v1beta1`. You can override the default version by setting the tfjobApiVersion param in the ksonnet app

```
ks param set tf-training-job tfjobApiVersion ${NEW_VERSION}
```

For GPU support set the `numGpu` param like:
```
# from the ks-app directory
ks param set tf-training-job numGpu 1
```

Here is a quick description for the `tf-training-job` component parameters:

- `image` string, docker image to use
- `mountPath` string, Volume mount path
- `numGpu` number, optional param, default to 0
- `numPs` number, Number of Parameter servers to use
- `numWorkers` number, Number of workers to use
- `pipelineConfigPath` string, the path to the pipeline config file in the volume mount
- `pvc` string, Persistent Volume Claim name to use
- `trainDir` string, Directory where the training outputs will be saved

To see the default values for the `tf-training-job` component params, please take a look at the [params.libsonnet](./ks-app/components/params.libsonnet) file.

## Next
[Monitor your job](monitor_job.md)
