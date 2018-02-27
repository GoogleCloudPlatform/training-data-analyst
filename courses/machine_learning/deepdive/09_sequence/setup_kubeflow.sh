#!/bin/sh

install_ksonnet() {
  wget https://github.com/ksonnet/ksonnet/releases/download/v0.8.0/ks_0.8.0_linux_amd64.tar.gz
  tar xvfz ks_0.8.0_linux_amd64.tar.gz
}

install_kubeflow() {
  rm -rf kubeflow-app
  ks init kubeflow-app
  cd kubeflow-app
  ks registry add kubeflow github.com/kubeflow/kubeflow/tree/master/kubeflow
  ks pkg install kubeflow/core
  ks pkg install kubeflow/tf-serving
  ks pkg install kubeflow/tf-job
  cd ..
}

create_kubeflow_core() {
  cd kubeflow-app
  kubectl create namespace ${KF_NAMESPACE}
  ks generate core kubeflow-core --name=kubeflow-core --namespace=${KF_NAMESPACE}
  ks env add nocloud
  ks env add cloud
  ks param set kubeflow-core cloud gke --env=cloud
  ks apply ${KF_ENV} -c kubeflow-core
  cd ..
}

deploy_model() {
  cd kubeflow-app
  MODEL_COMPONENT="servePoetry"
  MODEL_NAME="poetry"
  MODEL_PATH=gs://cloud-training-demos-ml/poetry/model_full/export/poetry
  echo "Deploying $MODEL_NAME from $MODEL_PATH"
  #ks generate tf-serving ${MODEL_COMPONENT} --name=${MODEL_NAME} --namespace=${KF_NAMESPACE} --model_path=${MODEL_PATH}
  ks apply ${KF_ENV} -c ${MODEL_COMPONENT}
  cd ..
}

setup_ingress() {
  cd kubeflow-app
  kubectl expose deployment poetry --type NodePort
  #gcloud compute addresses create mlpoetry-ingress --global  
  cat > /tmp/tfserving.yaml << EOF
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: tfservingIngress
  annotations:
    kubernetes.io/ingress.global-static-ip-name: "mlpoetry-ingress"
spec:
  backend:
    serviceName: poetry.poetry
    servicePort: 8000
EOF
  #kubectl create -f /tmp/tfserving.yaml
}

send_request() {
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
deploy_model
#setup_ingress
#send_request
