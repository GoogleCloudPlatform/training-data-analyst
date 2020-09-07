# general values
export PATH=$PATH:$LAB_DIR/bin:
export HOME=~

# GCP project
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} \
    --format="value(projectNumber)")

# Tools versions
export KUBECTX_VERSION=v0.7.0
export KOPS_VERSION=1.15.0

## Setting variables for GKE
export C1_NAME="central"
export C1_ZONE="us-central1-b"
export WORKLOAD_POOL=${PROJECT_ID}.svc.id.goog
export MESH_ID="proj-${PROJECT_NUMBER}"

# Variables for remote kops cluster
export C2_NAME="remote"
export C2_FULLNAME=$C2_NAME.k8s.local
export C2_ZONE="us-east1-b"
export NODE_COUNT=3
export NODE_SIZE=n1-standard-4
export KOPS_ZONES=$C2_ZONE
export INSTANCE_IP=$(curl -s api.ipify.org)
export INSTANCE_CIDR=$INSTANCE_IP/32
export KOPS_STORE=gs://$PROJECT_ID-kops-$C2_NAME