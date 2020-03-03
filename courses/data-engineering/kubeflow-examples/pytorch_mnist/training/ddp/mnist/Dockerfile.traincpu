FROM pytorch/pytorch:0.4_cuda9_cudnn7

WORKDIR /workspace
RUN chmod -R a+w /workspace
ADD ./mnist_DDP.py /opt/pytorch_dist_mnist/

ENTRYPOINT ["python", "-u", "/opt/pytorch_dist_mnist/mnist_DDP.py", "--modelpath", "/mnt/kubeflow-gcfs/pytorch/model"]

