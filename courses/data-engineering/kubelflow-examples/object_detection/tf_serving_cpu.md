## Serve the model using TF-Serving (CPU)

Before serving the model we need to perform a quick hack since the object detection export python api does not
generate a "version" folder for the saved model. This hack consists on creating a directory and move some files to it.
One way of doing this is by accessing to an interactive shell in one of your running containers and moving the data yourself

```
kubectl -n kubeflow exec -it pets-training-master-r1hv-0-i6k7c sh
mkdir /pets_data/exported_graphs/saved_model/1
cp /pets_data/exported_graphs/saved_model/* /pets_data/exported_graphs/saved_model/1
```

Configuring the pets-model component in 'ks-app':

```
MODEL_COMPONENT=pets-model
MODEL_PATH=/mnt/exported_graphs/saved_model
MODEL_STORAGE_TYPE=nfs
NFS_PVC_NAME=pets-pvc

ks param set ${MODEL_COMPONENT} modelPath ${MODEL_PATH}
ks param set ${MODEL_COMPONENT} modelStorageType ${MODEL_STORAGE_TYPE}
ks param set ${MODEL_COMPONENT} nfsPVC ${NFS_PVC_NAME}

ks apply ${ENV} -c pets-model
```

After applying the component you should see pets-model pod. Run:
```
kubectl -n kubeflow get pods | grep pets-model
```
That will output something like this:
```
pets-model-v1-57674c8f76-4qrqp      1/1       Running     0          4h
```
Take a look at the logs:
```
kubectl -n kubeflow logs pets-model-v1-57674c8f76-4qrqp
```
And you should see:
```
2018-06-21 19:20:32.325406: I tensorflow_serving/core/loader_harness.cc:86] Successfully loaded servable version {name: pets-model version: 1}
E0621 19:20:34.134165172       7 ev_epoll1_linux.c:1051]     grpc epoll fd: 3
2018-06-21 19:20:34.135354: I tensorflow_serving/model_servers/main.cc:288] Running ModelServer at 0.0.0.0:9000 ...
```
## Running inference using your model

Now you can use a gRPC client to run inference using your trained model as below!

First we need to install the dependencies (Ubuntu* 16.04 )
```
sudo apt-get install protobuf-compiler python-pil python-lxml python-tk
pip install tensorflow
pip install matplotlib
pip install tensorflow-serving-api
pip install numpy
pip install grpcio
```

Then download and compile TensorFlow models object detection utils API.
```
TF_MODELS=`pwd`
git clone https://github.com/tensorflow/models.git
cd models/research
protoc object_detection/protos/*.proto --python_out=.
PYTHONPATH=:${TF_MODELS}/models/research:${TF_MODELS}/models/research/slim:${PYTHONPATH}
```

At last, we need run below command in a different terminal session to port-forward to trained model server:
```
kubectl -n kubeflow port-forward service/pets-model 9000:9000
```

Now you can run the object detection client, and after that you should be seeing an image file in $OUT_DIR directory with the bounding boxes for detected objects.
```
#From examples/object_detection/serving_script directory
OUT_DIR=`pwd`
INPUT_IMG="image1.jpg"
python object_detection_grpc_client.py \
--server=localhost:9000 \
--input_image=${INPUT_IMG} \
--output_directory=${OUT_DIR} \
--label_map=${TF_MODELS}/models/research/object_detection/data/pet_label_map.pbtxt  \
--model_name=pets-model
```

## Next
[Serving the model with GPU](./tf_serving_gpu.md)
