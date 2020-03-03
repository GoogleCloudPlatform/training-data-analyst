# Serving an object detection model with GPU

## Setup

If you followed previous steps to train the model, skip to deploy [section](#deploy-serving-component).

Alternatively, you can do the following to deploy kubeflow and get a model.

Reference
[blog](https://cloud.google.com/blog/big-data/2017/09/performing-prediction-with-tensorflow-object-detection-models-on-google-cloud-machine-learning-engine)

### Deploy Kubeflow
Follow getting started
[guide](https://www.kubeflow.org/docs/started/getting-started/) to deploy
kubeflow.

### Prepare model
Download a model from [model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md).
The model should be in SavedModel format (including a `saved_model.pb` file and a
optional `variables/` folder.

```
wget http://download.tensorflow.org/models/object_detection/faster_rcnn_nas_coco_2018_01_28.tar.gz
tar -xzf faster_rcnn_nas_coco_2018_01_28.tar.gz
gsutil cp faster_rcnn_nas_coco_2018_01_28/saved_model/saved_model.pb gs://YOUR_BUCKET/YOUR_MODEL/1/
```

Or you can use the above model uploaded at `gs://kubeflow-examples-data/object-detection-coco/`.

## Deploy serving component

After deploying Kubeflow, you should have a ksonnet app; cd to that directory.
```
cd YOUR_KS_APP  # you can use the ks-app in this dir.
ks pkg install kubeflow/tf-serving  # If you haven't done it

ks generate tf-serving model1 --name=coco
ks param set model1 modelPath gs://YOUR_BUCKET/YOUR_MODEL/
ks param set model1 numGpus 1
ks param set model1 deployHttpProxy true
ks apply $ENV -c model1
```

## Send prediction
```
cd serving_script
python predict.py --url=YOUR_KF_HOST/models/coco
```

If you expose the TF Serving service as a LoadBalancer, change the url to
`EXTERNAL_IP:8000/model/coco:predict`

The script takes an input image (by default image1.jpg) and should save the result as `output.jpg`.
The output image has the bounding boxes for detected objects.
