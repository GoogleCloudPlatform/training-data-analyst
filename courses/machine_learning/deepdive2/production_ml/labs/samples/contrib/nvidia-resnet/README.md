# A simple GPU-accelerated ResNet Kubeflow pipeline
## Overview
This example demonstrates a simple end-to-end training & deployment of a Keras Resnet model on the CIFAR10 dataset utilizing the following technologies:
* [NVIDIA-Docker2](https://github.com/NVIDIA/nvidia-docker) to make the Docker containers GPU aware.
* [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) to allow Kubernetes to access GPU nodes.
* [TensorFlow-19.03](https://ngc.nvidia.com/catalog/containers/nvidia:tensorflow) containers from NVIDIA GPU Cloud container registry.
* [TensorRT](https://docs.nvidia.com/deeplearning/dgx/integrate-tf-trt/index.html) for optimizing the Inference Graph in FP16 for leveraging the dedicated use of Tensor Cores for Inference.
* [TensorRT Inference Server](https://github.com/NVIDIA/tensorrt-inference-server) for serving the trained model.

## System Requirements
* Ubuntu 16.04 and above
* NVIDIA GPU

## Quickstart
* Install NVIDIA Docker, Kubernetes and Kubeflow on your local machine (on your first run):
    * `sudo ./install_kubeflow_and_dependencies.sh`
* Build the Docker image of each pipeline component and compile the Kubeflow pipeline:
    * First, make sure `IMAGE` variable in `build.sh` in each component dir under `components` dir points to a  public container registry
    * Then, make sure the `image` used in each `ContainerOp` in `pipeline/src/pipeline.py` matches `IMAGE` in the step above
    * Then, make sure the `image` of the webapp Deployment in `components/webapp_launcher/src/webapp-service-template.yaml` matches `IMAGE` in `components/webapp/build.sh`
    * Then, `sudo ./build_pipeline.sh`
    * Note the `pipeline.py.tar.gz` file that appears in your working directory
* Determine the ambassador port:
    * `sudo kubectl get svc -n kubeflow ambassador`
* Open the Kubeflow UI on:
    * https://[local-machine-ip-address]:[ambassador-port]/
    * E.g. https://10.110.210.99:31342/
* Click on Pipeline Dashboard tab, upload the `pipeline.py.tar.gz` file you just compile and create a run
* Training takes about 20 minutes for 50 epochs and a web UI is deployed as part of the pipeline so user can interact with the served model
* Access the client web UI:
    * https://[local-machine-ip-address]:[kubeflow-ambassador-port]/[webapp-prefix]/
    * E.g. https://10.110.210.99:31342/webapp/
* Now you can test the trained model with random images and obtain class prediction and probability distribution

## Cleanup
Following are optional scripts to cleanup your cluster (useful for debugging) 
* Delete deployments & services from previous runs:
    * `sudo ./clean_utils/delete_all_previous_resources.sh`
* Uninstall Minikube and Kubeflow:
    * `sudo ./clean_utils/remove_minikube_and_kubeflow.sh`