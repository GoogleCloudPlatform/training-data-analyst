FROM ubuntu:16.04
MAINTAINER "David Sabater"

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

ADD proto/* /home/proto/

RUN pip --no-cache-dir install \
        Pillow \
        h5py \
        ipykernel \
        requests \
        grpcio \
        grpcio-tools \
        protobuf \
        numpy \
        tensorflow \
        tensorflow-serving-api \
        flask \
        && \
    python -m ipykernel.kernelspec && \
    python -m grpc.tools.protoc -I/home/proto --python_out=/home/proto \
    --grpc_python_out=/home/proto \
    --proto_path=/home/proto prediction.proto

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
