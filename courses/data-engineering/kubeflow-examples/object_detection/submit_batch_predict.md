# Launch object detection batch predict jobs using GPU

## Setup

Requirements:

 - K8s cluster with GPUs
 - Docker and Docker Registry
 - A Tensorflow model in SavedModel format

This example shows how to run batch prediction to do object detection on a
pre-trained model in a K8s cluster using GPU. See this [guide](https://www.kubeflow.org/docs/started/getting-started-gke/) to customize Kubeflow deployment to add GPU nodes.

Kubeflow batch-predict is [apache-beam](https://beam.apache.org/)-based and we
are using local runner to run the job in the K8s cluser in this example. One can, however,
choose different [runners](https://beam.apache.org/documentation/runners/capability-matrix/) to run the job remotely, such as on [Google Dataflow](https://cloud.google.com/dataflow/) service. As of July 2018, Google Dataflow does NOT support GPUs.

### Build and push the image
Use the pre-built image: [gcr.io/kubeflow-examples/batch-predict](https://gcr.io/kubeflow-examples/batch-predict) at Google Container Registry (GCR) or build a kubeflow batch predict image. Following is an example to build and host the image in GCR.

```
IMAGE="gcr.io/${YOUR_GCP_PROJECT}/batch-predict"

docker build -t ${IMAGE} -f ./Dockerfile.batch-predict .

gcloud docker -- push ${IMAGE}
```

### Prepare models
The model used in this example can be downloaded from
[gs://kubeflow-examples-data/object-detection-coco/image_string_model/saved_model](https://storage.googleapis.com/kubeflow-examples-data/object-detection-coco/image_string_model/saved_model/saved_model.pb). It is a slightly
modified version from the [faster RCNN object detection model](http://download.tensorflow.org/models/object_detection/faster_rcnn_nas_coco_2018_01_28.tar.gz) from [TensorFlow model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md). The model in this example accepts JPEG bytes as its input data.

Alternatively, you can follow the [steps](./export_tf_graph.md) to export your
own model from checkpoint files from your [training jobs](./submit_job.md), or download a pre-trained model in
SavedModel format from the model zoo. The latter accepts numpy arrays of images bits, instead of JPEG bytes.

Refer this [blog](https://cloud.google.com/blog/big-data/2017/09/performing-prediction-with-tensorflow-object-detection-models-on-google-cloud-machine-learning-engine) for exporting a model in SavedModel format, in particular, how to change the input format from the default.

### Prepare input data
In this example, the input tensor is JPEG image strings. So we pack the image bytes into TF-records. The input files contains 150 images and can be downloaded from [gs://kubeflow-examples-data/object-detection-coco/data/object-detection-images.tfrecord](https://storage.googleapis.com/kubeflow-examples-data/object-detection-coco/data/object-detection-images.small.tfrecord).

Refer this [blog](https://cloud.google.com/blog/big-data/2017/09/performing-prediction-with-tensorflow-object-detection-models-on-google-cloud-machine-learning-engine) for converting images into the input data the model can consume.

## Launch batch prediction job
Customize [batch-predict.yaml](./batch-predict/batch-predict.yaml) to add the
paths to the model, your input image files, the input format, and the output
locations. Simply run:

```
kubectl -n <your_name_space> apply -f ./batch-predict/batch-predict.yaml
```

**Arguments**

  * **input_file_patterns** The list of input files or file patterns, separated by commas.

  * **input_file_format** One of the following formats: json, tfrecord, and tfrecord_gzip. For the model in this example, the input is a JPEG-encoded image string tensor. The input file contains TF records of JPEG bytes. If you use a model from the [model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md) directly, the input is a numpy array instead. Then, your input file should contain multiple numeric arrays. Then the input format should be json. [Here](gs://kubeflow-examples-data/object-detection-coco/data/object-detection-images.json) is such a sample input, which contains two images.

  * **model_dir** The directory contains the model files in SavedModel format.

  * **batch_size** Number of records in one batch in the input data. Depending on the memory in your machine, it is
  recommend to be 1 to 4, up to 8 in this example.

  * **output_result_prefix** Output path to save the prediction results.

  * **output_error_prefix** Output path to save the prediction errors.

For other flags available to Kubeflow batch predict, please refer the [source
code](https://github.com/kubeflow/batch-predict/blob/master/kubeflow_batch_predict/dataflow/batch_prediction_main.py).

##  Monitor jobs
Once you submit the job, you can check the status and logs of the pod that runs the
batch-predict job:

```
kubectl log <your-pod-name>
```

When the pod status is "complete", check the result and error files you
specified when starting the job to see if the job is successful.

## Visualize detection results
You can use [this script](./serving_script/visualization_utils.py) to visualize the detection boxes from the prediction results files on images.
