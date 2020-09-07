# general values
export PATH=$PATH:$LAB_DIR/bin:
export HOME=~

# GCP project
export PROJECT_ID=$(gcloud config get-value project)

# Tools versions
export KUBECTX_VERSION=v0.7.0
export KOPS_VERSION=1.15.0

## Setting variables for GKE
export CLUSTER_NAME="central"
export CLUSTER_ZONE="us-central1-b"
export CLUSTER_KUBECONFIG=$LAB_DIR/$CLUSTER_NAME.context
export WORKLOAD_POOL=${PROJECT_ID}.svc.id.goog

# Variables for remote kops cluster
export REMOTE_CLUSTER_NAME_BASE="remote"
export REMOTE_CLUSTER_NAME=$REMOTE_CLUSTER_NAME_BASE.k8s.local
export KOPS_STORE=gs://$PROJECT_ID-kops-$REMOTE_CLUSTER_NAME_BASE
export REMOTE_KUBECONFIG=$LAB_DIR/remote.context
export NODE_COUNT=3
export NODE_SIZE=n1-standard-4
export ZONES=us-central1-a
