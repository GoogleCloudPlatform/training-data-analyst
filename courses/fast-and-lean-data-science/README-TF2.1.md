# Keras / TPU integration in Tensorflow 2.1 and above

 Tensorflow and Keras now offer:
 * support for TPUs
 * support for TPU pods
 * support for custom training loops on TPUs and TPU pods
 
 ## TPU-accelerated notebooks for professional data scientists
 
 You can  provision a TPU-accelerated notebook on Google's Cloud AI Platform. This script sums up the necessary gcloud commands:
 [create-tpu-deep-learning-vm.sh](https://raw.githubusercontent.com/GoogleCloudPlatform/training-data-analyst/master/courses/fast-and-lean-data-science/create-tpu-deep-learning-vm.sh)
 
 Detailed instructions at the bottom of this page.
 
 Cloud AI Platform notebooks work with TPU and TPU pods up to the largest TPUv3-2048 pod with 2048 cores.
 
 | *Cloud TPU v3-8 with 8 cores* | *TPU v3-2048 pod with 2048 cores* |
 | --- | --- |
 | ![TPU v3](https://cloud.google.com/images/products/tpu/cloud-tpu-v3-img_2x.png)  | ![TPU v3 pod](https://cloud.google.com/images/products/tpu/google-cloud-ai.png) |
  
The slide deck of the Oct 2019 Tensorflow World session is available here: 
 [bit.ly/keras-tpu-presentation](https://docs.google.com/presentation/d/e/2PACX-1vRqvlSpX5CVRC2oQ_e_nRNahOSPoDVL6I36kdjuPR_4y_tCPb-_k98Du1QXBwx4sBvVrzsCPulmuPn8/pub)
 
 TPUs are also available for free on [Colaboratory](https://colab.sandbox.google.com/github/GoogleCloudPlatform/training-data-analyst/blob/master/courses/fast-and-lean-data-science/07_Keras_Flowers_TPU_xception_fine_tuned_best.ipynb) (TPU v2-8)
 and [Kaggle](https://www.kaggle.com/mgornergoogle/five-flowers-with-keras-and-xception-on-tpu) (TPU v3-8).

## Sample Keras models

Sample notebooks from this repository. They open in Colaboratory for easy viewing. 

Regular Keras using model.fit():<br/>
[07_Keras_Flowers_TPU_xception_fine_tuned_best.ipynb](https://colab.sandbox.google.com/github/GoogleCloudPlatform/training-data-analyst/blob/master/courses/fast-and-lean-data-science/07_Keras_Flowers_TPU_xception_fine_tuned_best.ipynb)

Custom training loop, distributed:<br/>
[keras_flowers_customtrainloop_tf2.1.ipynb](https://colab.research.google.com/github/GoogleCloudPlatform/training-data-analyst/blob/master/courses/fast-and-lean-data-science/keras_flowers_customtrainloop_tf2.1.ipynb)

 End to end sample with TPU training, model export and deployment to AI Platform predictions:<br/>
 [01_MNIST_TPU_Keras.ipynb](https://colab.research.google.com/github/GoogleCloudPlatform/training-data-analyst/blob/master/courses/fast-and-lean-data-science/01_MNIST_TPU_Keras.ipynb)  

## Detailed instructions for provisioning a notebook with a Cloud TPU accelerator

Please use the above-mentioned script [create-tpu-deep-learning-vm.sh](https://raw.githubusercontent.com/GoogleCloudPlatform/training-data-analyst/master/courses/fast-and-lean-data-science/create-tpu-deep-learning-vm.sh)
to create an AI Platform Notebook VM along with a TPU in one go.
The script ensures that both your VM and the TPU have the same version of Tensorflow. Detailed steps:

 * Go to [Google cloud console](https://console.cloud.google.com/), create a new project with billing enabled.
 * Open cloud shell (>_ icon top right) so that you can type shell commands.
 * Get the script [create-tpu-deep-learning-vm.sh](https://raw.githubusercontent.com/GoogleCloudPlatform/training-data-analyst/master/courses/fast-and-lean-data-science/create-tpu-deep-learning-vm.sh), save it to a file, chmod u+x so that you can run it
 * Run `gcloud init` to set up your project and select a default zone that
 has TPUs. You can check TPU availability in different zones in [Google cloud console](https://console.cloud.google.com/)
 Compute Engine > TPUs > CREATE TPU NODE by playing with the zone and tpu type fields. For this
 demo, you can use an 8-core TPU or a 32-core TPU pod. Both TPU v2 and v3 will work.
 Select a zone that has v3-8, v2-32, v2-8 or v3-32 availability depending on what you want to test.
 * run the TPU and VM creation script:<br/>
 `./create-tpu-deep-learning-vm.sh choose-a-name --tpu-type v3-8`
 * If you get an error about an unavailable IP range, just run the script again, it will pick another one.
 * When the machines are up, go to [Google cloud console](https://console.cloud.google.com/) AI Platform > Notebooks
 and click OPEN JUPYTERLAB in front of the VM you just created.
 * Once in Jupyter, open a terminal and clone this repository:<br/>
 `git clone https://github.com/GoogleCloudPlatform/training-data-analyst.git`
 * Open one of the demo notebooks using the file browser in Jupyter:<br/>
 `training-data-analyst/courses/fast-and-lean-data-science/07_Keras_Flowers_TPU_xception_fine_tuned_best.ipynb`
 * Run through all the cells.
 * you can also try the custom training loop example notebook:<br/>
 `training-data-analyst/courses/fast-and-lean-data-science/keras_flowers_customtrainloop_tf2.1.ipynb`

TPU can also be provisioned manually in the [cloud console](https://console.cloud.google.com/). Go to
Compute Engine > TPUs > CREATE TPU NODE. Use the version selector to select the same version of Tensorflow as the one in your VM.
The script does the same thing but on the command line using the two
gcloud commands for creating a VM and a TPU. It adds a couple of perks:
the VM supports Jupyter notebooks out of the box, it has the TPU_NAME environment variable set pointing to your TPU,
and it can be upgraded to tf-nightly if you need cutting edge tech: add the --nightly parameter when you run the script.