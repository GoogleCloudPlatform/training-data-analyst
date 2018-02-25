#!/bin/sh

install_ksonnet() {
  wget https://github.com/ksonnet/ksonnet/releases/download/v0.8.0/ks_0.8.0_linux_amd64.tar.gz
  tar xvfz ks_0.8.0_linux_amd64.tar.gz
}

install_kubeflow() {
  rm -rf my-kubeflow
  ks init my-kubeflow
  cd my-kubeflow
  ks registry add kubeflow github.com/kubeflow/kubeflow/tree/master/kubeflow
  ks pkg install kubeflow/core
  ks pkg install kubeflow/tf-serving
  ks pkg install kubeflow/tf-job
  cd ..
}

create_kubeflow_core() {
  cd my-kubeflow
  kubectl create namespace ${KF_NAMESPACE}
  ks generate core kubeflow-core --name=kubeflow-core --namespace=${KF_NAMESPACE}
  ks env add nocloud
  ks env add cloud
  ks param set kubeflow-core cloud gke --env=cloud
  ks apply ${KF_ENV} -c kubeflow-core
  cd ..
}

deploy_model() {
  cd my-kubeflow
  MODEL_COMPONENT="servePoetry"
  MODEL_NAME="poetry"
  MODEL_PATH=$(gsutil ls gs://cloud-training-demos-ml/poetry/model_full/export/Servo | tail -1)
  echo "Deploying $MODEL_NAME from $MODEL_PATH"
  ks generate tf-serving ${MODEL_COMPONENT} --name=${MODEL_NAME} --namespace=${KF_NAMESPACE} --model_path=${MODEL_PATH}
  ks apply ${KF_ENV} -c ${MODEL_COMPONENT}
  cd ..
}

send_request() {
  CLUSTER_IP=$(kubectl get svc poetry -n=${KF_NAMESPACE} | awk '{print $3}' | tail -1)
  echo "Sending request to $CLUSTER_IP"
  curl -i -X POST -H 'Content-Type: application/json' -d '{"input": "all day long my heart trembles like a leaf"}' https://${CLUSTER_IP}:9000/
}

if [ -z "$GITHUB_TOKEN" ]; then
   echo "Please get a personal authorization token form GitHub. Otherwise, you'll run into rate limiting"
   echo "export GITHUB_TOKEN=<token>"
   exit -1
fi


export PATH=${PATH}:${PWD}/ks_0.8.0_linux_amd64/
export KF_NAMESPACE=poetry
export KF_ENV=cloud
#install_ksonnet
#install_kubeflow
#create_kubeflow_core
#deploy_model
send_request
