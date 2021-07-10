#!/bin/bash

#FIXME this is set to tf-user by default in order to work around lack of Serviceaccount setting in argo.
SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-tf-user}

create-kubeconfig ${SERVICE_ACCOUNT} > kubeconfig.tmp
cp kubeconfig.tmp ~/.kube/config

kubectl config set-cluster default --server="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}"

exec /bin/bash "$@"
