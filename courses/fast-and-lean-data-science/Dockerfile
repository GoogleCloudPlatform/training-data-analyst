# The base image for AI Platform Notebook instances
FROM gcr.io/deeplearning-platform-release/tf-gpu.1-13
# Stuff that should have been configured in the base image (bug)
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
# Upgrading to Tensorflow 2.0
RUN pip install tensorflow-gpu==2.0.0-beta1