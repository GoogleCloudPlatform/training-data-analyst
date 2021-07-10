#! /bin/bash

sudo su

# Install docker
apt-get update
apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository \
  "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) \
  stable"
apt-get update
apt-get -y install docker-ce docker-ce-cli containerd.io


# Clone repo
git clone https://github.com/GoogleCloudPlatform/training-data-analyst.git /home/theia-java-dataflow/training-data-analyst

# Pull containers
docker pull gcr.io/qwiklabs-resources/java-theia-ide-training-data-analyst
docker pull gcr.io/qwiklabs-resources/python-theia-ide-training-data-analyst
