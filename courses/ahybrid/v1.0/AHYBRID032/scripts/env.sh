# general values
export HOME=~
export PATH=$PATH:$LAB_DIR/bin:
export PROJECT_ID=$(gcloud config get-value project)

# gke cluster values
export C1_NAME="gke-west"
export C1_ZONE="us-west2-a"
export C1_NODES=2
export C1_SCOPE="https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append"
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} \
    --format="value(projectNumber)")
export WORKLOAD_POOL=${PROJECT_ID}.svc.id.goog
export MESH_ID="proj-${PROJECT_NUMBER}"

gcloud config set compute/zone $C1_ZONE