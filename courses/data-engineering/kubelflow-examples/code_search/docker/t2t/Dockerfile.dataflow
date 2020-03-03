# Dockerfile suitable for submitting Dataflow jobs and for runnin nmslib index creator.
#
# We don't use the Docker image used for running the training jobs
# because we have different versioning requirements.
FROM python:2.7-jessie

# These dependencies are primarily needed with Dataflow
# so we need to install them for Python2.
# We do this before copying the code because we don't want to have
# reinstall the requirements just because the code changed.
COPY src/requirements.dataflow.txt /tmp/requirements.dataflow.txt
RUN pip install -r /tmp/requirements.dataflow.txt
RUN pip install https://github.com/kubeflow/batch-predict/tarball/master

# Install nmslib requirements so that we can create the index
COPY src/requirements.nmslib.txt /tmp/requirements.nmslib.txt
RUN pip install -r /tmp/requirements.nmslib.txt

# install the spacy model
RUN python -m spacy download en

ADD src/code_search /app/code_search
ADD src             /src

# See: https://github.com/kubeflow/examples/issues/390
# Dataflow will try to build a source package locally and we need
# the path to match what we have in setup.py.
RUN ln -sf /src/requirements.dataflow.txt /src/requirements.txt

WORKDIR /src

ENV PYTHONIOENCODING=utf-8 T2T_USR_DIR=/app/code_search/t2t
