# general values
export PATH=$PATH:$LAB_DIR/bin:
export HOME=~

## Setting variables for cluster 1
export C1_NAME="west"
export C1_ZONE="us-west1-b"
export C1_NODES=2
export C1_SCOPE="https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append"

## Setting variables for cluster 2
export C2_NAME="east"
export C2_FULLNAME=$C2_NAME.k8s.local
export C2_ZONE="us-east1-b"
export C2_NODES=2
export C2_SCOPE="https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append"

## General variables
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} \
    --format="value(projectNumber)")
export WORKLOAD_POOL=${PROJECT_ID}.svc.id.goog
export MESH_ID="proj-${PROJECT_NUMBER}"
<<<<<<< Updated upstream

# Variables for remote kops cluster
export C2_NAME="remote"
export C2_FULLNAME=$C2_NAME.k8s.local
export C2_ZONE="us-west1-b"
=======
>>>>>>> Stashed changes
export NODE_COUNT=2
export NODE_SIZE=n1-standard-4