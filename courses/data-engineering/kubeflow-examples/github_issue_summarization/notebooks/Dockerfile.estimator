# TODO(jlewi): Can we merge with Dockerfile?
# This Dockerfile is used for training.
# We can probably use the same notebook Docker image if
# we just upgrade the notebook version. The conda environments
# however complicate things so it might be simpler just to
# have a separate image.
FROM python:3.6

# TODO(jlewi): We should probably pin version of TF and other libraries.
RUN pip install ktext==0.34
RUN pip install --upgrade annoy sklearn nltk tensorflow
RUN pip install --upgrade matplotlib ipdb
RUN pip install --upgrade google-cloud google-cloud-storage
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install unzip
RUN mkdir /issues
WORKDIR /issues
COPY ./ /issues/
RUN mkdir /model
RUN mkdir /data

CMD python train.py
