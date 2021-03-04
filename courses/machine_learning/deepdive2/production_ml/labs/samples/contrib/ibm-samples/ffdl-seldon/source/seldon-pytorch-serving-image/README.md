# PyTorch Gender Classification Seldon Serving container

# Wrap the Runtime Scorer
You can skip this step if you are happy to use the already packaged image ```aipipeline/seldon-pytorch:0.1``` from DockerHub.

The runtime MNIST scorer is contained within a standalone [python class Serving.py](./Serving.py). This needs to be packaged in a Docker container to run within Seldon. For this we use [Redhat's Source-to-image](https://github.com/openshift/source-to-image).

 * Install [S2I](https://github.com/openshift/source-to-image#installation)
 * From this `seldon-pytorch-serving-image` folder, run the following s2i build. You will need to change **aipipeline** to your DockerHub repo.
  ```shell
  s2i build . seldonio/seldon-core-s2i-python2:0.4 aipipeline/seldon-pytorch:0.1
  ```
 * Push image to DockerHub or your Docker registry that's accessible from the KubeFlow Pipeline cluster.
  ```shell
  docker push aipipeline/seldon-pytorch:0.1
  ```
