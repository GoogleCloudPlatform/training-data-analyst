FROM ubuntu:16.04
MAINTAINER "Daniel Sanche"

# add TF dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libfreetype6-dev \
        libpng12-dev \
        libzmq3-dev \
        pkg-config \
        python3 \
        python-dev \
        rsync \
        software-properties-common \
        unzip \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# add python dependencies
RUN curl -O https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py && \
    rm get-pip.py

RUN pip --no-cache-dir install \
        Pillow \
        h5py \
        ipykernel \
        numpy \
        tensorflow==1.7.0 \
        tensorflow-serving-api \
        flask \
        && \
    python -m ipykernel.kernelspec

# show python logs as they occur
ENV PYTHONUNBUFFERED=0

# add project files
ADD *.py /home/
ADD templates/* /home/templates/
ADD static/styles /home/static/styles/
RUN mkdir /home/static/tmp/
ADD static/scripts/ /home/static/scripts/

# start server on port 5000
WORKDIR /home/
EXPOSE 5000
ENTRYPOINT python flask_server.py
