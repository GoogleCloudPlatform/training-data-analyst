#!/usr/bin/env bash
# Common logic to initialize kubectl to use the underlying cluster

kubectl config set-cluster "${cluster}" --server=https://kubernetes.default --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
kubectl config set-credentials pipeline --token "$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
kubectl config set-context kubeflow --cluster "${cluster}" --user pipeline
kubectl config use-context kubeflow
ks env set "${ksEnvName}" --namespace="${namespace}"
