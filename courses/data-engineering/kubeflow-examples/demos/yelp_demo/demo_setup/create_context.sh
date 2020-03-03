#!/bin/bash
# create_context.sh $NAME $NAMESPACE
# Create a context for the current context but with the namespace given as an argument.
set -ex
CURRENT_CONTEXT=$(kubectl config current-context)
CURRENT_CLUSTER=$(kubectl config get-contexts $CURRENT_CONTEXT | tail -1 | awk '{print $3}')
CURRENT_USER=$(kubectl config get-contexts $CURRENT_CONTEXT | tail -1 | awk '{print $4}')

kubectl config set-context $1 \
   --namespace $2 \
   --cluster $CURRENT_CLUSTER \
   --user $CURRENT_USER

echo created context named: $1
kubectl config use-context $1