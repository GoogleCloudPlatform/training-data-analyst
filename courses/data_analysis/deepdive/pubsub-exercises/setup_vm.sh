#!/bin/bash
# This script sets up a GCE machine with the necessary dependencies to run the
# Cloud Pub/Sub SME training examples.
function run_and_check {
  "$@"
  status=$?
  if [ $status -ne 0 ]; then
    echo "Failed to run command $@"
    exit $status
  fi
}

run_and_check sudo apt-get update -y

# Install Java pieces.
run_and_check sudo apt-get install openjdk-8-jdk -y

run_and_check sudo update-alternatives --set javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac

run_and_check sudo update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java

run_and_check sudo apt-get install maven -y

run_and_check sudo apt-get update && sudo apt-get --only-upgrade install kubectl google-cloud-sdk google-cloud-sdk-datastore-emulator google-cloud-sdk-pubsub-emulator google-cloud-sdk-app-engine-go google-cloud-sdk-app-engine-java google-cloud-sdk-app-engine-python google-cloud-sdk-cbt google-cloud-sdk-bigtable-emulator google-cloud-sdk-datalab -y

# Install Python pieces.
run_and_check sudo apt-get install python3 -y

run_and_check curl https://bootstrap.pypa.io/get-pip.py | sudo python3

run_and_check sudo pip3 install --upgrade google-cloud-pubsub

echo "==================="
echo "SUCCESS"
