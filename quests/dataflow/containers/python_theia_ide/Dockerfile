# https://github.com/theia-ide/theia-apps/blob/master/theia-java-docker/Dockerfile
FROM theiaide/theia-python:latest

RUN curl -sSL https://sdk.cloud.google.com | bash


RUN apt-get update && apt-get install -y python3-pip

# Added for PubSub Academy to accept build_vm.sh file
RUN apt-get install sudo
RUN echo 'deb http://ftp.debian.org/debian stretch-backports main' | tee /etc/apt/sources.list.d/stretch-backports.list
RUN apt-get update

RUN /usr/bin/python3 -m pip install --upgrade pip
RUN /usr/bin/python3 -m pip install anytree google-cloud-pubsub faker geocoder pylint
RUN /usr/local/bin/python3 -m pip install -U pylint


ENV PATH $PATH:/root/google-cloud-sdk/bin:/home/theia/google-cloud-sdk/bin