#!/bin/sh

install_ksonnet() {
  wget https://github.com/ksonnet/ksonnet/releases/download/v0.8.0/ks_0.8.0_linux_amd64.tar.gz
  tar xvfz ks_0.8.0_linux_amd64.tar.gz
  export PATH=${PATH}:${PWD}/ks_0.8.0_linux_amd64/
}

install_kubeflow() {
  ks init my-kubeflow
  cd my-kubeflow
  ks registry add kubeflow github.com/kubeflow/kubeflow/tree/master/kubeflow
  ks pkg install kubeflow/core
  ks pkg install kubeflow/tf-serving
  ks pkg install kubeflow/tf-job
}

export KF_NAMESPACE=poetry
create_kubeflow_core() {
  kubectl create namespace ${KF_NAMESPACE}
  ks generate core kubeflow-core --name=kubeflow-core --namespace=${KF_NAMESPACE}
  ks env add nocloud
  ks env add cloud
  ks param set kubeflow-core cloud gke --env=cloud
  export KF_ENV=cloud
  ks apply ${KF_ENV} -c kubeflow-core
}

#install_ksonnet
#install_kubeflow
create_kubeflow_core

