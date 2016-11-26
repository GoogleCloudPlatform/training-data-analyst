#!/bin/bash

IMAGE=gcr.io/cloud-datalab/datalab:local   # release

# On linux, docker runs directly on host machine. It's important to bind
# to 127.0.0.1 only to prevent Datalab from accessible on the local network.
# On other platforms, bind to all ip addresses so VirtualBox can
# access it. Users need to make sure that their VirtualBox port forwarding
# setting only binds to 127.0.0.1.
if [ "$OSTYPE" == "linux"* ]; then
  PORTMAP="127.0.0.1:8081:8080"
else
  PORTMAP="8081:8080"
fi

# optionally, add a line like this to the docker run command:
# (change your project-id to match)
# if you don't do this, datalab will ask you to sign in and
# set a project-id
#   -e "PROJECT_ID=cloud-training-demos" \

docker pull $IMAGE
docker run -t \
   -p $PORTMAP \
   -v "${HOME}:/content" \
   $IMAGE &
