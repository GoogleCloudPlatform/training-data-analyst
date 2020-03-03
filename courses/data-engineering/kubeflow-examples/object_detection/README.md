# Distributed TensorFlow Object Detection Training and Serving on K8s with [Kubeflow](https://github.com/kubeflow/kubeflow)
This example demonstrates how to use `kubeflow` to train/serve an object detection model on an existing K8s cluster using
the [TensorFlow object detection API](https://github.com/tensorflow/models/tree/master/research/object_detection)

This example is based on the TensorFlow [Pets tutorial](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/running_pets.md).

## Steps:
1. [Setup a Kubeflow cluster](setup.md)
2. [Submit a distributed object detection training job](submit_job.md)
3. [Monitor your training job](monitor_job.md)
4. [Export model](export_tf_graph.md)
5. [Serve the model with GPU](tf_serving_gpu.md)
6. [Submit a batch prediction job using GPU](submit_batch_predict.md)
